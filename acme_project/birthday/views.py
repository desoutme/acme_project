from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)


from .forms import BirthdayForm, CongratulationForm
from .models import Birthday, Congratulation
from .utils import calculate_birthday_countdown


# def birthday(request, pk=None):
#    # Если в запросе указан pk (если получен запрос на редактирование объекта):
#    if pk is not None:
#        # Получаем объект модели или выбрасываем 404 ошибку.
#        instance = get_object_or_404(Birthday, pk=pk)
#    # Если в запросе не указан pk
#    # (если получен запрос к странице создания записи):
#    else:
#        # Связывать форму с объектом не нужно, установим значение None.
#        instance = None
#    # Передаём в форму либо данные из запроса, либо None.
#    # В случае редактирования прикрепляем объект модели.
#    form = BirthdayForm(
#        request.POST or None,
#        files=request.FILES or None,
#        instance=instance
#    )
#    # Остальной код без изменений.
#    context = {'form': form}
#    # Сохраняем данные, полученные из формы, и отправляем ответ:
#    if form.is_valid():
#        form.save()
#        birthday_countdown = calculate_birthday_countdown(
#            form.cleaned_data['birthday']
#        )
#        context.update({'birthday_countdown': birthday_countdown})
#    return render(request, 'birthday/birthday.html', context)


# def birthday_list(request):
#    # Получаем все объекты модели Birthday из БД.
#    birthdays = Birthday.objects.order_by('id')
#    paginator = Paginator(birthdays, 10)
#    page_number = request.GET.get('page')
#    page_obj = paginator.get_page(page_number)
#    # Передаём их в контекст шаблона.
#    context = {'page_obj': page_obj}
#    return render(request, 'birthday/birthday_list.html', context)


# def delete_birthday(request, pk):
#    # Получаем объект модели или выбрасываем 404 ошибку.
#    instance = get_object_or_404(Birthday, pk=pk)
#    # В форму передаём только объект модели;
#    # передавать в форму параметры запроса не нужно.
#    form = BirthdayForm(instance=instance)
#    context = {'form': form}
#    # Если был получен POST-запрос...
#    if request.method == 'POST':
#        # ...удаляем объект:
#        instance.delete()
#        # ...и переадресовываем пользователя на страницу со списком записей.
#        return redirect('birthday:list')
#    # Если был получен GET-запрос — отображаем форму.
#    return render(request, 'birthday/birthday.html', context)


class BirthdayMixin:
    model = Birthday
    success_url = reverse_lazy('birthday:list')


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class BirthdayListView(ListView):
    # Указываем модель, с которой работает CBV...
    model = Birthday
    # ...сортировку, которая будет применена при выводе списка объектов:
    queryset = Birthday.objects.prefetch_related(
        'tags'
    ).select_related('author')
    ordering = 'id'
    # ...и даже настройки пагинации:
    paginate_by = 10


class BirthdayCreateView(BirthdayMixin, CreateView):
    form_class = BirthdayForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BirthdayUpdateView(BirthdayMixin, OnlyAuthorMixin, UpdateView):
    form_class = BirthdayForm


class BirthdayDeleteView(BirthdayMixin, OnlyAuthorMixin, DeleteView):
    pass


class BirthdayDetailView(DetailView):
    model = Birthday

    def get_context_data(self, **kwargs):
        # Получаем словарь контекста:
        context = super().get_context_data(**kwargs)
        # Добавляем в словарь новый ключ:
        context['birthday_countdown'] = calculate_birthday_countdown(
            # Дату рождения берём из объекта в словаре context:
            self.object.birthday
        )
        # Записываем в переменную form пустой объект формы.
        context['form'] = CongratulationForm()
        # Запрашиваем все поздравления для выбранного дня рождения.
        context['congratulations'] = (
            # Дополнительно подгружаем авторов комментариев,
            # чтобы избежать множества запросов к БД.
            self.object.congratulations.select_related('author')
        )
        return context


@login_required
def add_comment(request, pk):
    # Получаем объект дня рождения или выбрасываем 404 ошибку.
    birthday = get_object_or_404(Birthday, pk=pk)
    # Функция должна обрабатывать только POST-запросы.
    form = CongratulationForm(request.POST)
    if form.is_valid():
        # Создаём объект поздравления, но не сохраняем его в БД.
        congratulation = form.save(commit=False)
        # В поле author передаём объект автора поздравления.
        congratulation.author = request.user
        # В поле birthday передаём объект дня рождения.
        congratulation.birthday = birthday
        # Сохраняем объект в БД.
        congratulation.save()
    # Перенаправляем пользователя назад, на страницу дня рождения.
    return redirect('birthday:detail', pk=pk)