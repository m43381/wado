from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DepartmentMissing
from people.models import People
from .forms import DepartmentMissingForm

@login_required
def department_missing_list(request):
    """Список освобождений кафедры"""
    if not hasattr(request.user, 'department'):
        messages.warning(request, 'У вас нет прав доступа к этому разделу')
        return redirect('home')
    
    missing_list = DepartmentMissing.objects.filter(
        person__department=request.user.department
    ).select_related('person').order_by('-start_date')
    
    return render(request, 'profiles/department/missing/department_missing_list.html', {
        'missing_list': missing_list,
        'department': request.user.department
    })

@login_required
def department_missing_add(request):
    """Добавление нового освобождения"""
    if not hasattr(request.user, 'department'):
        messages.warning(request, 'У вас нет прав доступа к этому разделу')
        return redirect('home')
    
    if request.method == 'POST':
        form = DepartmentMissingForm(request.POST)
        if form.is_valid():
            missing = form.save(commit=False)
            if missing.person.department != request.user.department:
                messages.error(request, 'Нельзя добавить освобождение для сотрудника другой кафедры')
                return redirect('department:missing:department_list')
            
            missing.save()
            messages.success(request, 'Освобождение успешно добавлено')
            return redirect('department:missing:department_list')
    else:
        form = DepartmentMissingForm()
        form.fields['person'].queryset = People.objects.filter(
            department=request.user.department
        ).order_by('full_name')
    
    return render(request, 'profiles/department/missing/department_missing_add.html', {
        'form': form
    })

@login_required
def department_missing_edit(request, pk):
    """Редактирование освобождения"""
    if not hasattr(request.user, 'department'):
        messages.warning(request, 'У вас нет прав доступа к этому разделу')
        return redirect('home')
    
    missing = get_object_or_404(DepartmentMissing, pk=pk)
    
    if missing.person.department != request.user.department:
        messages.error(request, 'Нельзя редактировать освобождение для сотрудника другой кафедры')
        return redirect('department:missing:department_list')
    
    if request.method == 'POST':
        form = DepartmentMissingForm(request.POST, instance=missing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Освобождение успешно обновлено')
            return redirect('department:missing:department_list')
    else:
        form = DepartmentMissingForm(instance=missing)
        form.fields['person'].queryset = People.objects.filter(
            department=request.user.department
        ).order_by('full_name')
    
    return render(request, 'profiles/department/missing/department_missing_edit.html', {
        'form': form,
        'missing': missing
    })

@login_required
def department_missing_delete(request, pk):
    """Удаление освобождения"""
    if not hasattr(request.user, 'department'):
        messages.warning(request, 'У вас нет прав доступа к этому разделу')
        return redirect('home')
    
    missing = get_object_or_404(DepartmentMissing, pk=pk)
    
    if missing.person.department != request.user.department:
        messages.error(request, 'Нельзя удалить освобождение для сотрудника другой кафедры')
        return redirect('department:missing:department_list')
    
    if request.method == 'POST':
        missing.delete()
        messages.success(request, 'Освобождение успешно удалено')
    
    return redirect('department:missing:department_list')