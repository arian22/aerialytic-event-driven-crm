import graphene # type: ignore
import requests # type: ignore
from graphene_django import DjangoObjectType # type: ignore
from kafka.producer import publish_event
from leads.models import Lead


USER_SERVICE_URL = "http://user-service:8000/graphql/"


# -------------------------
# Types
# -------------------------

class CompanyType(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()


class LeadType(DjangoObjectType):
    company = graphene.Field(CompanyType)

    class Meta:
        model = Lead
        fields = "__all__"

    def resolve_company(self, info):
        response = requests.post(
            USER_SERVICE_URL,
            headers={"Content-Type": "application/json"},
            json={
                "query": """
                    query GetCompany($id: UUID!) {
                        company(id: $id) {
                            id
                            name
                        }
                    }
                """,
                "variables": {"id": str(self.company_id)},
            },
        )

        if not response.ok:
            return None

        body = response.json()
        return body.get("data", {}).get("company")


# -------------------------
# Fetch user
# -------------------------

def fetch_user(user_id):
    response = requests.post(
        USER_SERVICE_URL,
        headers={"Content-Type": "application/json"},
        json={
            "query": """
                query ValidateUser($userId: UUID!) {
                    user(id: $userId) {
                        id
                        role
                        company {
                            id
                            children {
                                id
                            }
                        }
                    }
                }
            """,
            "variables": {"userId": str(user_id)},
        },
    )

    if not response.ok:
        raise Exception("User service error")

    body = response.json()
    data = body.get("data", {}).get("user")

    if not data:
        raise Exception("Invalid user")

    return data


# -------------------------
# Mutations
# -------------------------

class CreateLead(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        company_id = graphene.UUID(required=True)

    lead = graphene.Field(LeadType)

    def mutate(root, info, name, email, company_id):

        user_id = info.context.headers.get("x-user-id")
        if not user_id:
            raise Exception("Authentication required")

        user = fetch_user(user_id)

        role = user["role"]
        user_company_id = user["company"]["id"]
        children_ids = [c["id"] for c in user["company"]["children"]]

        # Company must exist
        company_check = requests.post(
            USER_SERVICE_URL,
            headers={"Content-Type": "application/json"},
            json={
                "query": """
                    query GetCompany($id: UUID!) {
                        company(id: $id) {
                            id
                        }
                    }
                """,
                "variables": {"id": str(company_id)},
            },
        )

        if not company_check.ok or not company_check.json().get("data", {}).get("company"):
            raise Exception("Company not found")

        # Child user cannot create lead outside own company
        if role == "CHILD_USER" and str(company_id) != user_company_id:
            raise Exception("Permission denied")

        # Parent admin access
        if role == "PARENT_ADMIN":
            allowed = [user_company_id] + children_ids
            if str(company_id) not in allowed:
                raise Exception("Permission denied")

        if Lead.objects.filter(email=email, company_id=company_id).exists():
            raise Exception("Lead already exists in this company")

        lead = Lead.objects.create(
            name=name,
            email=email,
            company_id=company_id,
        )

        publish_event(
            topic="lead.created",
            data={
                "lead_id": str(lead.id),
                "company_id": str(company_id),
                "status": lead.status,
            },
        )

        return CreateLead(lead=lead)


class UpdateLeadStatus(graphene.Mutation):
    class Arguments:
        lead_id = graphene.UUID(required=True)
        status = graphene.String(required=True)

    lead = graphene.Field(LeadType)

    def mutate(root, info, lead_id, status):

        user_id = info.context.headers.get("x-user-id")
        if not user_id:
            raise Exception("Authentication required")

        user = fetch_user(user_id)

        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            raise Exception("Lead not found")

        role = user["role"]
        user_company_id = user["company"]["id"]
        children_ids = [c["id"] for c in user["company"]["children"]]

        # Access control (exactly your old logic)
        if role == "CHILD_USER":
            if str(lead.company_id) != user_company_id:
                raise Exception("Permission denied")

        elif role == "PARENT_ADMIN":
            allowed = [user_company_id] + children_ids
            if str(lead.company_id) not in allowed:
                raise Exception("Permission denied")

        if status not in dict(Lead.Status.choices):
            raise Exception("Invalid status")

        lead.status = status
        lead.save()

        return UpdateLeadStatus(lead=lead)


# -------------------------
# Queries
# -------------------------

class Query(graphene.ObjectType):

    leads = graphene.List(
        LeadType,
        status=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int(),
        order_by=graphene.String(),
    )

    def resolve_leads(root, info, status=None, limit=None, offset=None, order_by=None):

        user_id = info.context.headers.get("x-user-id")
        if not user_id:
            raise Exception("Authentication required")

        user = fetch_user(user_id)

        role = user["role"]
        user_company_id = user["company"]["id"]
        children_ids = [c["id"] for c in user["company"]["children"]]

        queryset = Lead.objects.all()

        # Visibility rules
        if role == "CHILD_USER":
            queryset = queryset.filter(company_id=user_company_id)

        elif role == "PARENT_ADMIN":
            allowed = [user_company_id] + children_ids
            queryset = queryset.filter(company_id__in=allowed)

        if status:
            queryset = queryset.filter(status=status)

        if order_by:
            queryset = queryset.order_by(order_by)

        if offset:
            queryset = queryset[offset:]

        if limit:
            queryset = queryset[:limit]

        return queryset


class Mutation(graphene.ObjectType):
    create_lead = CreateLead.Field()
    update_lead_status = UpdateLeadStatus.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)