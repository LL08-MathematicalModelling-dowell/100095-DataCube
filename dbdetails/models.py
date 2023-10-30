# from django.db import models
# from django.contrib.auth.models import User
#
# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#
#
# class MongoDBModel(models.Model):
#     name = models.CharField(max_length=100)
#     user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#
#     class Meta:
#         db_table = 'mongodb_collection'
#         managed = False  # Don't create collections for this model
#         using = 'mongodb'