from sqladmin import Admin, ModelView
from .database import engine
from .models import User, Project, UserRole, ChatMessage, Prompt, Tag


def setup_admin(app):
    """Setup SQLAdmin with all model views."""
    admin = Admin(app, engine)

    # Admin model views
    class UserAdmin(ModelView, model=User):
        column_list = [
            User.id,
            User.username,
            User.email,
            User.is_active,
            User.is_superuser,
            User.created_at,
        ]
        column_searchable_list = [User.username, User.email]
        column_sortable_list = [User.id, User.username, User.created_at]

    class ProjectAdmin(ModelView, model=Project):
        column_list = [
            Project.id,
            Project.name,
            Project.description,
            Project.is_default,
            Project.is_active,
            Project.created_at,
        ]
        column_searchable_list = [Project.name]

    class UserRoleAdmin(ModelView, model=UserRole):
        column_list = [
            UserRole.id,
            UserRole.user_id,
            UserRole.project_id,
            UserRole.role,
            UserRole.created_at,
        ]

    class ChatMessageAdmin(ModelView, model=ChatMessage):
        column_list = [
            ChatMessage.id,
            ChatMessage.content,
            ChatMessage.session_id,
            ChatMessage.is_prompt_injection,
            ChatMessage.created_at,
        ]
        column_searchable_list = [ChatMessage.content]
        column_sortable_list = [ChatMessage.id, ChatMessage.created_at]

    class PromptAdmin(ModelView, model=Prompt):
        column_list = [Prompt.id, Prompt.project_id, Prompt.checked, Prompt.created_at]

    class TagAdmin(ModelView, model=Tag):
        column_list = [
            Tag.id,
            Tag.name,
            Tag.description,
            Tag.color,
            Tag.is_active,
            Tag.created_at,
        ]
        column_searchable_list = [Tag.name]

    # Add admin views
    admin.add_view(UserAdmin)
    admin.add_view(ProjectAdmin)
    admin.add_view(UserRoleAdmin)
    admin.add_view(ChatMessageAdmin)
    admin.add_view(PromptAdmin)
    admin.add_view(TagAdmin)

    return admin
