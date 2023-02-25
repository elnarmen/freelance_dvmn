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

    file = models.URLField(
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
        related_name='freelancer_orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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


class Message(models.Model):
    chat_id = models.IntegerField(
        'ID чата',
        db_index=True
    )

    customer = models.ForeignKey(
        Customer,
        verbose_name='Заказчик',
        related_name='customer_messages',
        on_delete=models.CASCADE
    )

    freelancer = models.ForeignKey(
        Customer,
        verbose_name='Исполнитель',
        related_name='freelancer_messagess',
        on_delete=models.SET_NULL,
        null=True
    )

    message = models.TextField(
        'Содержание сообщения'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return f'От {self.customer} к {self.freelancer}'