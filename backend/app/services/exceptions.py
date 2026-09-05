from app.core.jwt import ExpiredTokenError, InvalidTokenError, TokenError


class ServiceError(Exception):
    """Base domain exception for all Service Layer errors."""
    pass


class UserAlreadyExistsError(ServiceError):
    """Raised when attempting to create a user with an email that already exists."""
    pass


class RoleNotFoundError(ServiceError):
    """Raised when referencing a role ID that does not exist in the database."""
    pass


class AuthenticationError(ServiceError):
    """Base domain exception for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when email is unknown or candidate password fails verification.
    
    Protects against user enumeration by returning identical exception messages
    for both non-existent users and incorrect passwords.
    """
    pass


class InactiveUserError(AuthenticationError):
    """Raised when authenticating a user account marked inactive."""
    pass


class ResourceNotFoundError(ServiceError):
    """Raised when a requested master-data resource cannot be found."""
    pass


class DuplicateResourceError(ServiceError):
    """Raised when creating or updating a resource with a duplicate unique constraint (code, SKU, email, etc.)."""
    pass


class InvalidReferenceError(ServiceError):
    """Raised when referencing a foreign key resource that does not exist."""
    pass


class InactiveReferenceError(ServiceError):
    """Raised when attempting to associate a new entity with an inactive parent resource."""
    pass


class InventoryValidationError(ServiceError):
    """Raised when inventory quantities or operations violate domain constraints."""
    pass


class CommercialPolicyValidationError(ServiceError):
    """Raised when commercial policy definitions or thresholds violate domain constraints."""
    pass


class PolicyAmbiguityError(ServiceError):
    """Raised when conflicting or ambiguous overlapping commercial policies exist."""
    pass


class QuoteNotFoundError(ResourceNotFoundError):
    """Raised when a requested quotation cannot be found."""
    pass


class QuoteLineNotFoundError(ResourceNotFoundError):
    """Raised when a requested quotation line cannot be found."""
    pass


class QuoteNotEditableError(ServiceError):
    """Raised when attempting to edit a quotation in a non-editable state."""
    pass


class QuoteAccessDeniedError(ServiceError):
    """Raised when a user attempts an unauthorized operation on a quotation."""
    pass


class CurrencyMismatchError(ServiceError):
    """Raised when adding a product line whose currency does not match quotation currency."""
    pass


class QuotationValidationError(ServiceError):
    """Raised when quotation rules or parameters violate domain constraints."""
    pass


class OrderAlreadyExistsError(ServiceError):
    """Raised when an order already exists for a quotation."""
    pass


class ConfirmedVersionMissingError(ServiceError):
    """Raised when attempting to convert a quote without a confirmed version snapshot."""
    pass


class InvalidOrderStateError(ServiceError):
    """Raised when an order action is invalid for current order status."""
    pass


class InsufficientInventoryError(ServiceError):
    """Raised when requested inventory allocation exceeds available stock."""
    pass


class InvalidFulfillmentAllocationError(ServiceError):
    """Raised when fulfillment allocation details are invalid."""
    pass


class ReservationConflictError(ServiceError):
    """Raised when inventory reservation conflicts or fails."""
    pass


class BackorderNotFoundError(ResourceNotFoundError):
    """Raised when requested backorder does not exist."""
    pass


class ShipmentStateError(ServiceError):
    """Raised when shipment action is invalid for current shipment status."""
    pass


class BillingAlreadyInitializedError(ServiceError):
    """Raised when billing is already initialized for an order."""
    pass


class InvalidBillingPlanError(ServiceError):
    """Raised when billing plan configuration is invalid."""
    pass


class SubscriptionStateError(ServiceError):
    """Raised when subscription action is invalid for current subscription status."""
    pass


class InvalidProrationDateError(ServiceError):
    """Raised when proration date parameters are out of valid range."""
    pass


class InvalidPaymentAllocationError(ServiceError):
    """Raised when payment allocation total does not match payment amount or exceeds balance due."""
    pass


class OverpaymentError(ServiceError):
    """Raised when payment allocation exceeds invoice balance due."""
    pass


class CreditApplicationError(ServiceError):
    """Raised when applying a credit note fails validation."""
    pass


__all__ = [
    "ServiceError",
    "UserAlreadyExistsError",
    "RoleNotFoundError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "InactiveUserError",
    "TokenError",
    "InvalidTokenError",
    "ExpiredTokenError",
    "ResourceNotFoundError",
    "DuplicateResourceError",
    "InvalidReferenceError",
    "InactiveReferenceError",
    "InventoryValidationError",
    "CommercialPolicyValidationError",
    "PolicyAmbiguityError",
    "QuoteNotFoundError",
    "QuoteLineNotFoundError",
    "QuoteNotEditableError",
    "QuoteAccessDeniedError",
    "CurrencyMismatchError",
    "QuotationValidationError",
    "OrderAlreadyExistsError",
    "ConfirmedVersionMissingError",
    "InvalidOrderStateError",
    "InsufficientInventoryError",
    "InvalidFulfillmentAllocationError",
    "ReservationConflictError",
    "BackorderNotFoundError",
    "ShipmentStateError",
    "BillingAlreadyInitializedError",
    "InvalidBillingPlanError",
    "SubscriptionStateError",
    "InvalidProrationDateError",
    "InvalidPaymentAllocationError",
    "OverpaymentError",
    "CreditApplicationError",
]



