
import csv
import calendar

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages
from django.http import HttpResponse

from .models import Expense
from .forms import ExpenseForm


@login_required(login_url='/login/')
def dashboard(request):
    today = timezone.localdate()
    expenses = Expense.objects.filter(user=request.user)

    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    monthly_expense = expenses.filter(
        date__year=today.year,
        date__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or 0

    today_expense = expenses.filter(
        date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    budget = 10000
    budget_percentage = min(float(monthly_expense) / budget * 100, 100)
    remaining_budget = max(budget - float(monthly_expense), 0)

    recent_expenses = expenses.order_by('-date', '-created_at')[:5]

    category_data = list(
        expenses.filter(
            date__year=today.year,
            date__month=today.month
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('category')
    )

    context = {
        'total_expense': total_expense,
        'monthly_expense': monthly_expense,
        'today_expense': today_expense,
        'budget': budget,
        'budget_percentage': budget_percentage,
        'remaining_budget': remaining_budget,
        'recent_expenses': recent_expenses,
        'category_data': category_data,
    }

    return render(request, 'expenses/dashboard.html', context)


@login_required(login_url='/login/')
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('transactions')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'page_title': 'Add Expense',
        'button_text': 'Save Expense',
    })


@login_required(login_url='/login/')
def transactions(request):
    expenses = Expense.objects.filter(user=request.user)

    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()

    valid_categories = [
        choice[0] for choice in Expense.CATEGORY_CHOICES
    ]

    if search_query:
        expenses = expenses.filter(title__icontains=search_query)

    if selected_category in valid_categories:
        expenses = expenses.filter(category=selected_category)
    else:
        selected_category = ''

    expenses = expenses.order_by('-date', '-created_at')

    total_amount = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'expenses': expenses,
        'search_query': search_query,
        'selected_category': selected_category,
        'categories': Expense.CATEGORY_CHOICES,
        'filtered_total': total_amount,
        'expense_count': expenses.count(),
    }

    return render(request, 'expenses/transactions.html', context)


@login_required(login_url='/login/')
def expense_edit(request, pk):
    expense = get_object_or_404(
        Expense, pk=pk, user=request.user
    )

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)

        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('transactions')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'page_title': 'Edit Expense',
        'button_text': 'Update Expense',
    })


@login_required(login_url='/login/')
def expense_delete(request, pk):
    expense = get_object_or_404(
        Expense, pk=pk, user=request.user
    )

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('transactions')

    return render(request, 'expenses/expense_confirm_delete.html', {
        'expense': expense
    })


@login_required(login_url='/login/')
def monthly_reports(request):
    today = timezone.localdate()
    user_expenses = Expense.objects.filter(user=request.user)

    years = list(
        user_expenses.dates('date', 'year', order='DESC')
    )
    available_years = sorted(
        {item.year for item in years} | {today.year},
        reverse=True
    )

    try:
        selected_year = int(request.GET.get('year', today.year))
        if selected_year not in available_years:
            selected_year = today.year
    except (ValueError, TypeError):
        selected_year = today.year

    try:
        selected_month = int(request.GET.get('month', today.month))
        if selected_month < 1 or selected_month > 12:
            selected_month = today.month
    except (ValueError, TypeError):
        selected_month = today.month

    report_expenses = user_expenses.filter(
        date__year=selected_year,
        date__month=selected_month
    ).order_by('-date', '-created_at')

    total_amount = report_expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    category_data = list(
        report_expenses.values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
    )

    context = {
        'report_expenses': report_expenses,
        'total_amount': total_amount,
        'expense_count': report_expenses.count(),
        'category_data': category_data,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'month_name': calendar.month_name[selected_month],
        'available_years': available_years,
        'months': [
            (i, calendar.month_name[i]) for i in range(1, 13)
        ],
    }

    return render(request, 'expenses/reports.html', context)


@login_required(login_url='/login/')
def download_report(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        if year < 1900 or year > 9998 or month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, 'Please select a valid month and year.')
        return redirect('monthly_reports')

    expenses = Expense.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).order_by('date', 'created_at')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')
    response['Content-Disposition'] = (
        f'attachment; filename="expense_report_{year}_{month:02d}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Amount (INR)', 'Category',
        'Date', 'Description'
    ])

    for expense in expenses:
        writer.writerow([
            expense.title,
            expense.amount,
            expense.category,
            expense.date.strftime('%Y-%m-%d'),
            expense.description,
        ])

    return response


def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Account created successfully. Please log in.'
            )
            return redirect('user_login')
    else:
        form = UserCreationForm()

    return render(request, 'expenses/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        return render(request, 'expenses/login.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'expenses/login.html')


def user_logout(request):
    logout(request)
    return redirect('user_login')
