from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout


def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "You must be logged in to access this page.")
            return redirect(f"/signin?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_only(view_fun):
    def wrapper_func(request,*args,**kwargs):
        if request.user.is_authenticated:
            if request.user.role =="admin":
                return view_fun(request,*args, **kwargs)
            if request.user.role == "user":
                return redirect("user_index")
            if request.user.role == "manager":
                return redirect("manager_index")
            else:
                logout(request)
                messages.error(request,"Your account has not belongs to company account please contact site administrator for further assistance ")
                return redirect("signin")
        else:
            messages.warning(request, "You must be logged in to access this page.")
            return redirect(f"/signin?next={request.path}")

    return wrapper_func

