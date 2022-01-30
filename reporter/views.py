from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView, ListView, DeleteView
from django.contrib import messages
import os
from datetime import date
from datetime import datetime

from yametrep.settings import BASE_DIR
from .forms import ProjectForm, ProjectCreateForm
from .models import Project, Link
from .utils import get_data_and_dates_metrika, write_csv, export_to_gspread, delete_file_gspread, share_file_gspread
from accounts.models import CustomUser


class ProjectDelete(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'reporter/project_delete.html'
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        links = self.object.links.all()
        if links:
            for link in links:
                delete_file_gspread(link)
                link.delete()

        messages.success(request, 'Проект удален')
        self.object.delete()
        return HttpResponseRedirect(success_url)


def share_link(request):
    if request.method == 'POST':
        link_pk = int(request.POST['link_id'])
        email = request.POST['email']
        link = get_object_or_404(Link, pk=link_pk)
        redirect_id = link.project_set.all()[0].id
        share_file_gspread(link, email)

        return HttpResponseRedirect(f'/{redirect_id}/')


@login_required
def delete_link(request, pk):
    link = get_object_or_404(Link, pk=pk)
    redirect_id = link.project_set.all()[0].id
    delete_file_gspread(link)
    link.delete()
    messages.success(request, 'Документ удален')
    return HttpResponseRedirect(f'/{redirect_id}/')


class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    queryset = Project.objects.select_related('owner').all()
    template_name = 'reporter/project_list.html'


class ProjectAdd(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'reporter/project_add.html'
    form_class = ProjectCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProjectCreateForm()
        return context

    def post(self, request, *args, **kwargs):
        project = self.form_class(request.POST)

        if project.is_valid():
            new_project = project.save()
            user = CustomUser.objects.get(pk=request.POST['user_id'])
            new_project.owner = user
            new_project.save()

            return redirect(new_project)


class ProjectEdit(LoginRequiredMixin, UpdateView):
    template_name = 'reporter/project_edit.html'
    form_class = ProjectForm

    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Project.objects.get(pk=id)

    def post(self, request, *args, **kwargs):
        project = self.form_class(request.POST)

        if project.is_valid():
            edited_project = project.save()
            messages.success(request, 'Новые настройки сохранены')
            return redirect(edited_project)


class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'reporter/project_detail.html'

    def get_object(self):
        obj = get_object_or_404(
            self.model.objects.prefetch_related(
                Prefetch('links', queryset=Link.objects.order_by('-id'))
            ),
            pk=self.kwargs['pk'],
        )
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['today'] = date.today().strftime('%Y-%m-%d')
        return context


@login_required
def create_report(request):
    if request.method == 'POST':

        project_name = request.POST['name']
        ids = request.POST['counter']
        months = request.POST['months']
        ids, months = int(ids), int(months)
        token = request.POST['token']
        date1 = request.POST['start-date']
        date2 = request.POST['end-date']
        email = request.POST['email']

        if datetime.strptime(date1, '%Y-%m-%d') > datetime.strptime(date2, '%Y-%m-%d'):
            messages.error(request, 'Дата конца отчета должна быть позже, чем дата начала отчета')
            return HttpResponseRedirect(f'/{request.POST["project_id"]}/')

        data_from_metrika = get_data_and_dates_metrika(token, ids, date1, date2, months)

        if data_from_metrika is None:
            messages.error(request, 'Ошибка доступа к Метрике! Проверьте параметры или свяжитесь с поддержкой.')
            return HttpResponseRedirect(f'/{request.POST["project_id"]}/')

        data, dates = data_from_metrika

        write_csv(data, dates, project_name)

        file_exists = os.path.exists(BASE_DIR / f'reporter/tempfiles/{project_name}.csv')

        if file_exists:
            path = BASE_DIR / f'reporter/tempfiles/{project_name}.csv'
            link, name, gs_id = export_to_gspread(path, project_name, email)
            link_obj = Link.objects.create(name=name, text=link, gs_id=gs_id)
            Project.objects.get(id=request.POST["project_id"]).links.add(link_obj)

        else:
            # write log with error
            messages.error(request, 'Ой, ошибка! Проверьте параметры или свяжитесь с поддержкой.')
            return HttpResponseRedirect(f'/{request.POST["project_id"]}/')
    messages.success(request, 'Новый отчет успешно создан')
    return HttpResponseRedirect(f'/{request.POST["project_id"]}/')
