from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView, ListView

from .forms import ProjectForm, ProjectCreateForm
from .models import Project, Link

from .utils import get_data_and_dates_metrika, write_csv, export_to_gspread
import os
from datetime import date
from accounts.models import CustomUser

@login_required
def delete_link(request, pk):
    link = get_object_or_404(Link, pk=pk)
    redirect_id = link.project_set.all()[0].id

    link.delete()

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


class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project

    template_name = 'reporter/project_detail.html'

    def get_object(self):
        obj = get_object_or_404(
            self.model.objects.prefetch_related('links'),
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
        print(request.POST)
        project_name = request.POST['name']
        ids = request.POST['counter']
        months = request.POST['months']
        ids, months = int(ids), int(months)
        token = request.POST['token']
        date1 = request.POST['start-date']
        date2 = request.POST['end-date']
        email = request.POST['email']

        data, dates = get_data_and_dates_metrika(token, ids, date1, date2, months)

        write_csv(data, dates, project_name)

        file_exists = os.path.exists(f'/home/sobbaka/projects/yametrep/reporter/tempfiles/{project_name}.csv')

        if file_exists:
            path = f'/home/sobbaka/projects/yametrep/reporter/tempfiles/{project_name}.csv'
            link, name = export_to_gspread(f'/home/sobbaka/projects/yametrep/reporter/tempfiles/{project_name}.csv', project_name, email)
            link_obj = Link.objects.create(name=name, text=link)
            Project.objects.get(id=request.POST["project_id"]).links.add(link_obj)

            print(link)
        else:
            # HttpResponseRedirect to error page
            print('error')

    return HttpResponseRedirect(f'/{request.POST["project_id"]}/')