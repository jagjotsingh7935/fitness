from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class AdminOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            print("---- Permission Check Start ----")
            
            print(f"User object: {request.user}")
            print(f"User ID: {getattr(request.user, 'id', None)}")
            print(f"Username: {getattr(request.user, 'username', None)}")
            print(f"Is Authenticated: {request.user.is_authenticated}")
            print(f"Is Admin: {getattr(request.user, 'is_admin', None)}")
            print(f"Is Superuser: {getattr(request.user, 'is_superuser', None)}")

            if not (request.user.is_authenticated and 
                    (getattr(request.user, 'is_admin', False) or request.user.is_superuser)):
                
                print("❌ Permission Denied")
                raise PermissionDenied("You do not have permission to access this")
            
            print("✅ Permission Granted")
            print("---- Permission Check End ----")
            return True

        except AttributeError as e:
            print(f"⚠️ Error checking admin permission: {str(e)}")
            raise PermissionDenied("You do not have permission to access this")
        

class CustomModelPermissions(BasePermission):
    def has_permission(self, request, view):
        try:
            # Allow superusers and admins to access all actions
            if request.user.is_authenticated and (request.user.is_superuser or request.user.is_admin):
                return True

            # Try to get the model from the view's permission_model attribute
            model = getattr(view, 'permission_model', None)

            # If no permission_model is set, try to infer from serializer or queryset
            if not model:
                # Check if the view has a serializer_class
                serializer_class = getattr(view, 'serializer_class', None)
                if serializer_class:
                    # Get the model from the serializer's Meta class
                    model = getattr(serializer_class.Meta, 'model', None)

                if not model:
                    try:
                        serializer_class = view.get_serializer_class()
                        model = getattr(serializer_class.Meta, 'model', None)
                    except (AttributeError, NotImplementedError):
                        pass

                # Fallback to queryset if available (for GenericAPIView)
                if not model and hasattr(view, 'queryset'):
                    model = view.queryset.model

            if not model:
                raise PermissionDenied("Cannot determine model for permission check")

            # Get model name and app label
            model_name = model._meta.model_name.lower()
            app_label = model._meta.app_label

            # Map HTTP methods to permission codenames
            method_permission_map = {
                'GET': f'can_view_{model_name}',
                'HEAD': f'can_view_{model_name}',
                'OPTIONS': f'can_view_{model_name}',
                'POST': f'create_{model_name}',
                'PUT': f'update_{model_name}',
                'PATCH': f'update_{model_name}',
                'DELETE': f'can_delete_{model_name}',
            }

            # Get the required permission for the request method
            required_permission = method_permission_map.get(request.method)
            if not required_permission:
                raise PermissionDenied("You do not have permission to access this")

            # Check if the user has the required permission
            full_permission = f'{app_label}.{required_permission}'
            if not request.user.has_perm(full_permission):
                raise PermissionDenied(f"You do not have permission to access this: {full_permission}")
            return True
        except AttributeError as e:
            print(f"Error checking model permission: {str(e)}")
            raise PermissionDenied("You do not have permission to access this")