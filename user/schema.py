from django.contrib.auth import get_user_model

import graphene
from graphene_django import DjangoObjectType
from .models import EmailActivation

User = get_user_model()


class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude_fields = ('password',)


class Query(graphene.ObjectType):
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        full_name = graphene.String(required=True)
        username = graphene.String(required=False)

    def mutate(self, info, password, email, full_name, username=None):
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            username=username,
            password=password,
        )
        return CreateUser(user=user)

class VerifyKey(graphene.Mutation):
    email = graphene.String()
    class Arguments:
        key = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, key, email):
        verified_email = EmailActivation.objects.verify_key(key=key, email=email)
        return VerifyKey(email=verified_email)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    verify_key = VerifyKey.Field()
