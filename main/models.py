from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser

from .utilities import get_timestamp_path, send_new_comment_notification
from ckeditor.fields import RichTextField

class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True, db_index=True, verbose_name='Прошел активацию?')
    send_messages = models.BooleanField(default=True, verbose_name='Слать оповещения о новых комментариях?')
    avatar = models.ImageField(blank=True, upload_to='avatars', verbose_name='Аватар') 

    def delete(self, *args, **kwargs):
        for bb in self.bb_set.all():
            bb.delete()
        super().delete(*args, **kwargs)

    class Meta(AbstractUser.Meta):
        pass


class Rubric(models.Model):
    name = models.CharField(max_length=20, db_index=True, unique=True, verbose_name='Название')
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name='Порядок')
    super_rubric = models.ForeignKey('SuperRubric', on_delete=models.PROTECT, null=True, blank=True,
                                     verbose_name='Надрубрика')


class SuperRubricManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=True)


class SuperRubric(Rubric):
    objects = SuperRubricManager()

    def __str__(self):
        return self.name

    class Meta:
        proxy = True
        ordering = ('order', 'name')
        verbose_name = 'Надрубрика'
        verbose_name_plural = 'Надрубрики'


class SubRubricManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(super_rubric__isnull=False)


class SubRubric(Rubric):
    objects = SubRubricManager()

    def __str__(self):
        return '%s - %s' % (self.super_rubric.name, self.name)

    class Meta:
        proxy = True
        ordering = ('super_rubric__order', 'super_rubric__name', 'order', 'name')
        verbose_name = 'Подрубрика'
        verbose_name_plural = 'Подрубрики'


def generate_filename(instance, filename):
    filename = instance.title + '.pdf'
    return "{0}/{1}".format(instance, filename)

def generate_filename_jpg(instance, filename):
    filename = instance.title + '.jpg'
    return "{0}/{1}".format(instance, filename)    


CATEGORIES = (
    (1, 'Русский'),
    (2, 'Английский')
)


FORMAT = (
    (1, 'PDF'),
    (2, 'FB2'),
    (3, 'EPUB'),
    (4, 'MOBI'),  
    (5, 'TXT'),
    (6, 'DJVU'),
    (7, 'DOC'),
    (8, 'ZIP'),
    (9, 'RAR'),
)

class Bb(models.Model):
    title = models.CharField(max_length=40, verbose_name='Название книги')
    writer = models.CharField(max_length=40, verbose_name='Автор книги')
    rubric = models.ForeignKey(SubRubric, on_delete=models.PROTECT, verbose_name='Язык программирования')
    relise = models.CharField(max_length=4, verbose_name='Год выхода')
    lang_category = models.IntegerField(choices=CATEGORIES, default=1, db_index=True, verbose_name='Язык')
    content = RichTextField(verbose_name='Описание')
    image = models.ImageField(blank=True, upload_to=generate_filename_jpg, verbose_name='Обложка')
    formate = models.IntegerField(choices=FORMAT, default=1, db_index=True, verbose_name='Формат файла')
    file_book = models.FileField(blank=True, upload_to=generate_filename, verbose_name='Файл')
    slug = models.CharField(max_length=100, blank=True, verbose_name='Ссылка с другого ресурса')
    author = models.ForeignKey(AdvUser, on_delete=models.CASCADE, verbose_name='Добавил книгу')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Выводить в списке?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Опубликовано')



    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Книги'
        verbose_name = 'Книга'
        ordering = ['-created_at']

class Comment(models.Model):
    bb = models.ForeignKey(Bb, on_delete=models.CASCADE, verbose_name='Книга')
    author = models.CharField(max_length=30, verbose_name='Автор')
    content = models.TextField(verbose_name='Содержание')
    is_active = models.BooleanField(default=True, db_index=True, verbose_name='Выводить комментарий?')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Опубликован')

    class Meta:
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'
        ordering = ['created_at']


def post_save_dispatcher(sender, **kwargs):
    author = kwargs['instance'].bb.author
    if kwargs['created'] and author.send_messages:
        send_new_comment_notification(kwargs['instance'])


post_save.connect(post_save_dispatcher, sender=Comment)
