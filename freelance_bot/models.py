from django.db import models

# Create your models here.
class Tariff(models.Model):
    name = models.CharField(
        'Наименование тарифа',
        max_length=20,
        help_text='Эконом, Стандарт, VIP'
    )

    description = models.TextField(
        'Описание тарифа'
    )

    price = models.IntegerField(
        'Стоимость тарифа'
    )

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.name


class Customer(models.Model):
    first_name = models.CharField(
        'Имя',
        max_length=20,
        blank=True
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=20,
        blank=True
    )

    nickname = models.CharField(
        'Никнейм в телеграме',
        max_length=30,
        db_index=True
    )

    is_freelancer = models.BooleanField(
        'Фрилансер',
        default=False
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.nickname


class Order(models.Model):
    CREATE = 'create'
    WORK = 'work'
    CLOSED = 'closed'
    
    STATUS_CHOICES = [
        (CREATE, 'Создан'),
        (WORK, 'В работе'),
        (CLOSED, 'Завершен'),
    ]

    name = models.CharField(
        'Название заказа',
        max_length=50,
        db_index=True
    )

    description = models.TextField(
        'Описание заказа'
    )

    file = models.FileField(
        'Файл',
        null=True,
        blank=True
    )

    customer = models.ForeignKey(
        Customer,
        verbose_name='Заказчик',
        related_name='customer_orders',
        on_delete=models.CASCADE
    )

    freelancer = models.ForeignKey(
        Customer,
        verbose_name='Исполнитель',
        related_name='freelances_orders',
        on_delete=models.SET_NULL,
        null=True
    )

    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return self.name