from django.shortcuts import render,HttpResponse,redirect
from rbac import models
from app01 import models
from rbac.service import initial_permission
from django.db.models import Q
import datetime
def login(request):
    if request.method == 'GET':
        return render(request,'login.html')
    else:
        u=request.POST.get('username')
        p=request.POST.get('password')
        info=models.UserInfo.objects.filter(user__password=p,user__username=u).first()

        if info:
            request.session['userinfo']={'username':u,'password':p,'nid':info.user_id}
            initial_permission(request,info.id)
            return render(request,'index.html',{'info':info})
        else:
            return redirect('/login.html')

def index(request):
    if request.session.get('userinfo'):
        return render(request,'index.html')
    else:
        return redirect('/login.html')

def trouble(request):
    if request.permission_code == 'GET':
        all_list=models.Order.objects.all().values('id','status','detail','title')
        return render(request,'trouble.html',{'all_list':all_list})
    elif request.permission_code == 'ADD':
        if request.method == 'GET':
            return render(request,'trouble_add.html')
        else:
            title=request.POST.get('title')
            detail=request.POST.get('detail')
            models.Order.objects.create(title=title,detail=detail,create_user_id=request.session['userinfo']['nid'],status=1)
            return redirect('/trouble.html')
    elif request.permission_code == 'DEL':
        id=request.GET.get('nid')
        models.Order.objects.filter(id=id).delete()
        return redirect('/trouble.html')
    elif request.permission_code == 'POST':
        if request.method == 'GET':
            id=request.GET.get('nid')
            v=models.Order.objects.filter(id=id).first()
            return render(request,'trouble_post.html',{'v':v})
        else:
            id=request.GET.get('nid')
            print(id)
            title=request.POST.get('title')
            print(title)
            detail=request.POST.get('detail')
            print(detail)
            models.Order.objects.filter(id=id).update(title=title,detail=detail)
            return redirect('/trouble.html')

def troublekill(request):
    if request.permission_code == 'GET':
        nid=request.session['userinfo']['nid']
        ##查找当前用户未处理列表和全部未解决列表
        obj=models.Order.objects.filter(Q(status=1)|Q(processor_id=nid)).order_by('status')
        return render(request,'troublekill.html',{'obj':obj})
    else:
        if request.method == 'GET':
            nid=request.GET.get('nid')
            status_choice=models.Order.status_choice
            ##抢单成功后未处理列表
            if models.Order.objects.filter(id=nid,status=2,processor_id=request.session['userinfo']['nid']):
                obj=models.Order.objects.filter(id=nid).first()
                return render(request,'troublekill_update.html',{'obj':obj,'status_choice':status_choice})
            else:
                ##开抢
                v=models.Order.objects.filter(id=nid,status=1).update(status=2,processor_id=request.session['userinfo']['nid'])
                if not v:
                    return HttpResponse('手慢了...')
                return redirect('troublekill.html')

        else:
            nid=request.GET.get('nid')
            print(nid)
            do=request.POST.get('do')
            print(do)
            models.Order.objects.filter(id=nid).update(status=3,solution=do)
            return redirect('troublekill.html')

def rbac(request):
    return render(request,'hightest.html')












