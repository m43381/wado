from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Duty
from .forms import DutyForm

@login_required
def duty_list(request):
    dutys = Duty.objects.all().order_by('duty_name')
    return render(request, 'profiles/commandant/duty/duty_list.html', {
        'dutys': dutys,
    })

@login_required
def add_duty(request):
    if request.method == 'POST':
        form = DutyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Наряд успешно добавлен')
            return redirect('commandant:duty:list')
    else:
        form = DutyForm()
    
    return render(request, 'profiles/commandant/duty/add_duty.html', {
        'form': form,
    })

@login_required
def edit_duty(request, pk):
    duty = get_object_or_404(Duty, pk=pk)
    
    if request.method == 'POST':
        form = DutyForm(request.POST, instance=duty)
        if form.is_valid():
            form.save()
            messages.success(request, 'Наряд успешно обновлен')
            return redirect('commandant:duty:list')
    else:
        form = DutyForm(instance=duty)
    
    return render(request, 'profiles/commandant/duty/edit_duty.html', {
        'form': form,
        'duty': duty
    })

@login_required
def delete_duty(request, pk):
    duty = get_object_or_404(Duty, pk=pk)
    if request.method == 'POST':
        duty.delete()
        messages.success(request, f'Наряд "{duty.duty_name}" успешно удален')
    return redirect('commandant:duty:list')