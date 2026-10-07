from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Task(models.Model):
    status_choices=[('Todo','todo'),('In Progress','in progress'),('Completed','completed')]
    priority_choices=[('Low','low'),('Medium','medium'),('High','high')]
    user=models.ForeignKey(User, on_delete=models.CASCADE,related_name='tasks')
    title=models.CharField(max_length=200)
    description=models.TextField(blank=True)
    status=models.CharField(max_length=20,choices=status_choices,default='Todo')
    priority=models.CharField(max_length=10,choices=priority_choices,default='Medium')
    due_date=models.DateField(null=True,blank=True)
    created_date=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title