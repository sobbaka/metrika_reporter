from django.db import models
from django.urls import reverse

from accounts.models import CustomUser


class Project(models.Model):
    name = models.CharField('Название', max_length=155)
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='projects',
        verbose_name ='Владелец',
        null=True,
        blank=True
    )
    email = models.EmailField('Email для расшаривания')
    counter = models.IntegerField('Счетчик метрики')
    token = models.CharField('Token апи метрики', max_length=155)
    links = models.ManyToManyField('Link', verbose_name ='Ссылки', blank=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={"pk": self.id})

    def project_update_url(self):
        return reverse('project_edit', kwargs={"pk": self.id})


class Link(models.Model):
    name = models.CharField('Название', max_length=155)
    text = models.CharField('Ссылка', max_length=255)
    file = models.FileField(upload_to="csv_files/", null=True, blank=True)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return self.name