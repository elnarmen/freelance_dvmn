from django.db import models
from django.utils import timezone

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
    telegram_id = models.IntegerField(
        'Telegram ID',
        db_index=True
    )

    first_name = models.CharField(
        'Имя',
        max_length=20,
        null=True,
        blank=True
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=20,
        null=True,
        blank=True
    )

    nickname = models.CharField(
        'Никнейм в телеграме',
        max_length=30,
        null=True,
        blank=True,
        db_index=True
    )

    tariff = models.ForeignKey(
        Tariff,
        verbose_name='Подписка',
        on_delete=models.PROTECT,
        null=True,
        blank=True
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
    class OrderStatus(models.TextChoices):
        CREATE = 'create', 'Создан'
        WORK = 'work', 'В работе'
        CLOSED = 'closed', 'Завершен'

    name = models.CharField(
        'Название заказа',
        max_length=50,
        db_index=True
    )

    description = models.TextField(
        'Описание заказа'
    )

    telegram_file_id = models.CharField(
        'ID файла в телеграм',
        max_length=200,
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
        related_name='freelancer_orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=OrderStatus.choices,
        db_index=True,
        default=OrderStatus.CREATE
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return self.name


class Message(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='chat_messages',
        on_delete=models.CASCADE
    )

    message_from = models.ForeignKey(
        Customer,
        verbose_name='От кого',
        related_name='from_messages',
        on_delete=models.CASCADE
    )

    message_to = models.ForeignKey(
        Customer,
        verbose_name='Kому',
        related_name='to_messagess',
        on_delete=models.SET_NULL,
        null=True
    )

    message = models.TextField(
        'Содержание сообщения'
    )

    created_at = models.DateTimeField(
        'Время и дата сообщения',
        default=timezone.now,
        db_index=True
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return f'От {self.message_from} к {self.message_to}. Дата: {self.created_at}'