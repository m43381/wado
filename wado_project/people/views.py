from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import People
from .forms import PeopleForm

@login_required
def department_staff(request):
    staff = People.objects.filter(department=request.user.department).order_by('full_name')
    return render(request, 'profiles/department/department_staff.html', {
        'staff': staff,
        'department': request.user.department
    })

@login_required
def add_staff(request):
    if request.method == 'POST':
        form = PeopleForm(request.POST)
        if form.is_valid():
            new_person = form.save(commit=False)
            new_person.department = request.user.department
            new_person.faculty = request.user.faculty
            new_person.save()
            messages.success(request, 'Сотрудник успешно добавлен')
            return redirect('department:people:staff')
    else:
        form = PeopleForm()
    
    return render(request, 'profiles/department/add_staff.html', {
        'form': form,
        'department': request.user.department
    })

@login_required
def edit_staff(request, pk):
    staff_member = get_object_or_404(People, pk=pk, department=request.user.department)
    
    if request.method == 'POST':
        form = PeopleForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные сотрудника обновлены')
            return redirect('department:people:staff')
    else:
        form = PeopleForm(instance=staff_member)
    
    return render(request, 'profiles/department/edit_staff.html', {
        'form': form,
        'staff_member': staff_member
    })

@login_required
def delete_staff(request, pk):
    staff_member = get_object_or_404(People, pk=pk, department=request.user.department)
    if request.method == 'POST':
        staff_member.delete()
        messages.success(request, 'Сотрудник удален')
    return redirect('department:people:staff')