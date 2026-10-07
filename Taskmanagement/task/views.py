from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from task.models import Task
from task.serializers import UserSerializer, TaskSerializer, LoginSerializer
from django.views import View

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    'message':
                        'Registration successful',
                    'token':
                        token.key
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username,password=password)
        if user is None:
            return Response(
                {
                    'error':'Invalid username or password'},status=status.HTTP_401_UNAUTHORIZED)
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                'message':'Login successful',
                'token': token.key},
            status=status.HTTP_200_OK)

class TaskListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tasks = Task.objects.filter(user=request.user).order_by('-created_date')
        search = request.GET.get('search')
        status_filter = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        if search:
            tasks = tasks.filter(title__icontains=search)
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)
        serializer = TaskSerializer(tasks,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class TaskDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk, user):
        try:
            return Task.objects.get(pk=pk,user=user)
        except Task.DoesNotExist:
            return None
    def get(self, request, pk):
        task = self.get_object(pk,request.user)
        if task is None:
            return Response(
                {
                    'error':'Task not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TaskSerializer(task)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def put(self, request, pk):
        task = self.get_object(pk,request.user)
        if task is None:
            return Response(
                {
                    'error':'Task not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TaskSerializer(task,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        task = self.get_object(pk,request.user)
        if task is None:
            return Response(
                {
                    'error':'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class Home(View):
    def get(self,request):
        return render(request,'home.html')

class LoginPageView(View):
    def get(self, request):
        return render(request, 'login.html')
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request, user)
            return redirect('/task/')
        return render(request,'login.html',{'error': 'Invalid username or password'})

from django.contrib.auth.models import User
class RegisterPageView(View):
    def get(self, request):
        return render(request, 'register.html')
    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not username or not password:
            return render(request,'register.html',{'error': 'Username and password are required'})
        if User.objects.filter(username=username).exists():
            return render(request,'register.html',{'error': 'Username already exists'})
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return redirect('/login/')

from django.contrib.auth.mixins import LoginRequiredMixin
class TaskDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user).order_by('-created_date')
        search = request.GET.get('search')
        status_filter = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        if search:
            tasks = tasks.filter(title__icontains=search)
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)
        context = {
            'tasks': tasks,
            'search': search or '',
            'selected_status': status_filter or '',
            'selected_priority': priority_filter or '',
        }
        return render(request,'dashboard.html',context)

class TaskCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'task_create.html')
    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description')
        task_status = request.POST.get('status')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        if not title:
            return render(
                request,'task_create.html',{
                    'error': 'Title is required'
                }
            )
        Task.objects.create(user=request.user,title=title,description=description,status=task_status,priority=priority,due_date=due_date if due_date else None)
        return redirect('/task/')

class TaskUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk,user=request.user)
        except Task.DoesNotExist:
            return redirect('/task/')
        return render(
            request,'task_edit.html',{'task': task})
    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk,user=request.user)
        except Task.DoesNotExist:
            return redirect('/task/')
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.status = request.POST.get('status')
        task.priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        if due_date:
            task.due_date = due_date
        else:
            task.due_date = None
        task.save()
        return redirect('/task/')
class TaskDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            task = Task.objects.get(
                pk=pk,
                user=request.user
            )
        except Task.DoesNotExist:
            return redirect('/task/')
        task.delete()
        return redirect('/task/')

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('/login/')
