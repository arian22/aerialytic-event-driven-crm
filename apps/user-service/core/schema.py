import graphene # type: ignore
from graphene_django import DjangoObjectType # type: ignore
from users.models import Company, User


class CompanyType(DjangoObjectType):
    parent = graphene.Field(lambda: CompanyType)
    children = graphene.List(lambda: CompanyType)

    def resolve_parent(self, info):
        return self.parent

    def resolve_children(self, info):
        return self.children.all()

    class Meta:
        model = Company
        fields = "__all__"


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"


# -------------------------
# Mutations
# -------------------------

class CreateCompany(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        parent_id = graphene.UUID(required=False)

    company = graphene.Field(CompanyType)

    def mutate(root, info, name, parent_id=None):

        parent = None
        if parent_id:
            parent = Company.objects.filter(id=parent_id).first()
            if not parent:
                raise Exception("Parent company not found")

        company = Company.objects.create(
            name=name,
            parent=parent
        )

        return CreateCompany(company=company)


class CreateUser(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        role = graphene.String(required=True)
        company_id = graphene.UUID(required=True)

    user = graphene.Field(UserType)

    def mutate(root, info, email, role, company_id):

        company = Company.objects.filter(id=company_id).first()
        if not company:
            raise Exception("Company not found")

        user = User.objects.create(
            email=email,
            role=role,
            company=company
        )

        return CreateUser(user=user)


# -------------------------
# Queries
# -------------------------

class Query(graphene.ObjectType):
    companies = graphene.List(CompanyType)
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.UUID(required=True))

    company = graphene.Field(CompanyType, id=graphene.UUID(required=True))

    def resolve_company(root, info, id):
        return Company.objects.filter(id=id).first()

    def resolve_companies(root, info):
        return Company.objects.all()

    def resolve_users(root, info):
        return User.objects.all()

    def resolve_user(root, info, id):
        return User.objects.filter(id=id).first()


class Mutation(graphene.ObjectType):
    create_company = CreateCompany.Field()
    create_user = CreateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)