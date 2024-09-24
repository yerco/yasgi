from sqlalchemy.exc import IntegrityError

from src.controllers.base_controller import BaseController
from src.event_bus import Event

from demo_app.di_setup import di_container
from demo_app.models.user import User


async def home_controller(event: Event):
    # Resolve services from the DI container
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')

    users = await orm_service.all(User)

    controller = BaseController(event)

    context = {'title': 'Welcome', 'text': 'Hello from the template!', 'users': users}
    rendered_content = template_service.render_template('home.html', context)

    await controller.send_html(rendered_content, status=200)
