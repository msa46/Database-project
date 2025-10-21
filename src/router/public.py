from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from pony.orm import db_session
import logging
import traceback

from ..database.models import ExtraType, IngredientType, DeliveryStatus, OrderStatus, DiscountCode, User, Customer, Employee, DeliveryPerson, Pizza, Order
from ..database.views import MenuView, DietaryFilter
from ..database.queryManager import QueryManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/v1/public", tags=["public endpoints"])

# Pydantic models for request/response
class PizzaInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    stock: int

class IngredientInfo(BaseModel):
    id: int
    name: str
    price: float
    type: str

class ExtraInfo(BaseModel):
    id: int
    name: str
    price: float
    type: str

class DiscountCodeInfo(BaseModel):
    code: str
    percentage: float
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    used: bool
    type: str
    description: str

class DeliveryPersonInfo(BaseModel):
    id: int
    username: str
    status: str

class OrderInfo(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: str
    postal_code: str

class EarningsReport(BaseModel):
    group_by: str
    filter_value: str
    total_earnings: float
    average_earnings: float

class TopPizzaInfo(BaseModel):
    pizza_id: int
    pizza_name: str
    total_quantity: int

# Enhanced models for moved secured features
class SecuredInfoResponse(BaseModel):
    message: str
    user_type: str
    user_id: int
    username: str
    email: str

class IngredientInfo(BaseModel):
    name: str
    price: float
    type: str

class PizzaInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    dietary_type: str
    stock: int
    ingredients: List[IngredientInfo] = []

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedPizzaResponse(BaseModel):
    pizzas: List[PizzaInfo]
    pagination: PaginationInfo

class CustomerInfo(BaseModel):
    id: int
    username: str
    email: str

class OrderInfo(BaseModel):
    id: int
    status: str
    created_at: str
    postal_code: str

class CustomerSpecificResponse(SecuredInfoResponse):
    loyalty_points: int
    birthday_order: bool
    available_pizzas: List[PizzaInfo] = []
    pizza_pagination: Optional[PaginationInfo] = None
    available_extras: List[ExtraInfo] = []

class EmployeeSpecificResponse(SecuredInfoResponse):
    position: str
    salary: float
    customers: List[CustomerInfo] = []

class DeliveryPersonSpecificResponse(EmployeeSpecificResponse):
    status: str
    orders: List[OrderInfo] = []

class PizzaQuantity(BaseModel):
    pizza_id: int
    quantity: int

class MultiplePizzaOrderRequest(BaseModel):
    pizza_quantities: List[PizzaQuantity]
    extra_ids: Optional[List[int]] = None
    discount_code: Optional[str] = None
    postal_code: Optional[str] = None

class OrderItemInfo(BaseModel):
    type: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float

class DiscountInfo(BaseModel):
    code: str
    percentage: float
    amount: float

class MultiplePizzaOrderResponse(BaseModel):
    order_id: int
    status: str
    message: str
    total_price: float
    items: List[OrderItemInfo]
    discount: Optional[DiscountInfo] = None
    created_at: str
    postal_code: str

# Menu endpoints
@router.get("/pizzas", response_model=List[PizzaInfo])
async def get_all_pizzas():
    """Get all available pizzas without authentication"""
    try:
        logger.debug("Getting all pizzas from public endpoint")
        pizzas = QueryManager.get_all_pizzas()
        
        pizza_list = []
        for pizza in pizzas:
            pizza_info = PizzaInfo(
                id=pizza.id,
                name=pizza.name,
                description=pizza.description if hasattr(pizza, 'description') else None,
                stock=pizza.stock
            )
            pizza_list.append(pizza_info)
        
        logger.debug(f"Retrieved {len(pizza_list)} pizzas")
        return pizza_list
        
    except Exception as e:
        logger.error(f"Error getting all pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pizzas"
        )

@router.get("/pizzas/vegan", response_model=List[PizzaInfo])
async def get_vegan_pizzas():
    """Get all vegan pizzas without authentication"""
    try:
        logger.debug("Getting vegan pizzas from public endpoint")
        pizzas = QueryManager.get_vegan_pizzas()
        
        pizza_list = []
        for pizza in pizzas:
            pizza_info = PizzaInfo(
                id=pizza.id,
                name=pizza.name,
                description=pizza.description if hasattr(pizza, 'description') else None,
                stock=pizza.stock
            )
            pizza_list.append(pizza_info)
        
        logger.debug(f"Retrieved {len(pizza_list)} vegan pizzas")
        return pizza_list
        
    except Exception as e:
        logger.error(f"Error getting vegan pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vegan pizzas"
        )

@router.get("/pizzas/vegetarian", response_model=List[PizzaInfo])
async def get_vegetarian_pizzas():
    """Get all vegetarian pizzas without authentication"""
    try:
        logger.debug("Getting vegetarian pizzas from public endpoint")
        pizzas = QueryManager.get_vegetarian_pizzas()
        
        pizza_list = []
        for pizza in pizzas:
            pizza_info = PizzaInfo(
                id=pizza.id,
                name=pizza.name,
                description=pizza.description if hasattr(pizza, 'description') else None,
                stock=pizza.stock
            )
            pizza_list.append(pizza_info)
        
        logger.debug(f"Retrieved {len(pizza_list)} vegetarian pizzas")
        return pizza_list
        
    except Exception as e:
        logger.error(f"Error getting vegetarian pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vegetarian pizzas"
        )

@router.get("/pizzas/{pizza_id}/ingredients", response_model=List[IngredientInfo])
async def get_pizza_ingredients(pizza_id: int):
    """Get ingredients for a specific pizza without authentication"""
    try:
        logger.debug(f"Getting ingredients for pizza {pizza_id} from public endpoint")
        ingredients = QueryManager.get_pizza_ingredients(pizza_id)
        
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_info = IngredientInfo(
                id=ingredient.id,
                name=ingredient.name,
                price=ingredient.price,
                type=ingredient.type.value if hasattr(ingredient.type, 'value') else str(ingredient.type)
            )
            ingredient_list.append(ingredient_info)
        
        logger.debug(f"Retrieved {len(ingredient_list)} ingredients for pizza {pizza_id}")
        return ingredient_list
        
    except ValueError as e:
        logger.error(f"Value error getting pizza ingredients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting pizza ingredients: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pizza ingredients"
        )

@router.get("/pizzas/{pizza_id}/price", response_model=Dict[str, float])
async def get_pizza_price(pizza_id: int):
    """Get calculated price for a specific pizza without authentication"""
    try:
        logger.debug(f"Getting price for pizza {pizza_id} from public endpoint")
        price = QueryManager.calculate_pizza_price(pizza_id)
        
        logger.debug(f"Retrieved price {price} for pizza {pizza_id}")
        return {"price": price}
        
    except ValueError as e:
        logger.error(f"Value error getting pizza price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting pizza price: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pizza price"
        )

# Extras endpoints
@router.get("/extras/drinks", response_model=List[ExtraInfo])
async def get_all_drinks():
    """Get all drink extras without authentication"""
    try:
        logger.debug("Getting all drinks from public endpoint")
        drinks = QueryManager.get_all_drinks()
        
        drink_list = []
        for drink in drinks:
            drink_info = ExtraInfo(
                id=drink.id,
                name=drink.name,
                price=drink.price,
                type=drink.type.value if hasattr(drink.type, 'value') else str(drink.type)
            )
            drink_list.append(drink_info)
        
        logger.debug(f"Retrieved {len(drink_list)} drinks")
        return drink_list
        
    except Exception as e:
        logger.error(f"Error getting all drinks: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drinks"
        )

@router.get("/extras/desserts", response_model=List[ExtraInfo])
async def get_all_desserts():
    """Get all dessert extras without authentication"""
    try:
        logger.debug("Getting all desserts from public endpoint")
        desserts = QueryManager.get_all_desserts()
        
        dessert_list = []
        for dessert in desserts:
            dessert_info = ExtraInfo(
                id=dessert.id,
                name=dessert.name,
                price=dessert.price,
                type=dessert.type.value if hasattr(dessert.type, 'value') else str(dessert.type)
            )
            dessert_list.append(dessert_info)
        
        logger.debug(f"Retrieved {len(dessert_list)} desserts")
        return dessert_list
        
    except Exception as e:
        logger.error(f"Error getting all desserts: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve desserts"
        )

@router.get("/extras", response_model=List[ExtraInfo])
async def get_extras_by_type(extra_type: str):
    """Get extras by type without authentication"""
    try:
        logger.debug(f"Getting extras of type {extra_type} from public endpoint")
        
        # Convert string to ExtraType enum
        if extra_type.lower() == "drink":
            type_enum = ExtraType.Drink
        elif extra_type.lower() == "dessert":
            type_enum = ExtraType.Dessert
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid extra type. Must be 'drink' or 'dessert'"
            )
        
        extras = QueryManager.get_extras_by_type(type_enum)
        
        extra_list = []
        for extra in extras:
            extra_info = ExtraInfo(
                id=extra.id,
                name=extra.name,
                price=extra.price,
                type=extra.type.value if hasattr(extra.type, 'value') else str(extra.type)
            )
            extra_list.append(extra_info)
        
        logger.debug(f"Retrieved {len(extra_list)} extras of type {extra_type}")
        return extra_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extras by type: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve extras"
        )

# Ingredients endpoint
@router.get("/ingredients", response_model=List[IngredientInfo])
async def get_all_ingredients():
    """Get all ingredients without authentication"""
    try:
        logger.debug("Getting all ingredients from public endpoint")
        ingredients = QueryManager.get_all_ingredients()
        
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_info = IngredientInfo(
                id=ingredient.id,
                name=ingredient.name,
                price=ingredient.price,
                type=ingredient.type.value if hasattr(ingredient.type, 'value') else str(ingredient.type)
            )
            ingredient_list.append(ingredient_info)
        
        logger.debug(f"Retrieved {len(ingredient_list)} ingredients")
        return ingredient_list
        
    except Exception as e:
        logger.error(f"Error getting all ingredients: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ingredients"
        )

# Delivery endpoints
@router.get("/delivery/persons/available", response_model=List[DeliveryPersonInfo])
async def get_available_delivery_persons():
    """Get all available delivery persons without authentication"""
    try:
        logger.debug("Getting available delivery persons from public endpoint")
        delivery_persons = QueryManager.get_available_delivery_persons()
        
        dp_list = []
        for dp in delivery_persons:
            dp_info = DeliveryPersonInfo(
                id=dp.id,
                username=dp.username,
                status=dp.status.value if hasattr(dp.status, 'value') else str(dp.status)
            )
            dp_list.append(dp_info)
        
        logger.debug(f"Retrieved {len(dp_list)} available delivery persons")
        return dp_list
        
    except Exception as e:
        logger.error(f"Error getting available delivery persons: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available delivery persons"
        )

@router.get("/delivery/persons/random", response_model=Optional[DeliveryPersonInfo])
async def get_random_delivery_person():
    """Get a random delivery person without authentication"""
    try:
        logger.debug("Getting random delivery person from public endpoint")
        delivery_person = QueryManager.get_random_delivery_person()
        
        if not delivery_person:
            logger.debug("No delivery persons found")
            return None
        
        dp_info = DeliveryPersonInfo(
            id=delivery_person.id,
            username=delivery_person.username,
            status=delivery_person.status.value if hasattr(delivery_person.status, 'value') else str(delivery_person.status)
        )
        
        logger.debug(f"Retrieved random delivery person: {delivery_person.username}")
        return dp_info
        
    except Exception as e:
        logger.error(f"Error getting random delivery person: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve random delivery person"
        )

# Discount code endpoints
@router.get("/discounts/{code}", response_model=DiscountCodeInfo)
async def get_discount_code_details(code: str):
    """Get discount code details without authentication"""
    try:
        logger.debug(f"Getting discount code details for {code} from public endpoint")
        details = QueryManager.get_discount_code_details(code)
        
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount code not found"
            )
        
        discount_info = DiscountCodeInfo(
            code=details['code'],
            percentage=details['percentage'],
            valid_from=details['valid_from'].isoformat() if details['valid_from'] else None,
            valid_until=details['valid_until'].isoformat() if details['valid_until'] else None,
            used=details['used'],
            type=details['type'],
            description=details['description']
        )
        
        logger.debug(f"Retrieved discount code details for {code}")
        return discount_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discount code details: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve discount code details"
        )

@router.post("/discounts/create", response_model=Dict[str, str])
async def create_discount_code():
    """Create a new discount code and return it"""
    try:
        logger.debug("Creating new discount code from public endpoint")
        
        with db_session:
            # Generate a random discount code
            import secrets
            code = secrets.token_hex(8).upper()
            
            # Set validity period (30 days from now)
            from datetime import datetime, timedelta
            now = datetime.now()
            valid_until = now + timedelta(days=30)
            
            # Create discount code with 10% discount
            discount_code = DiscountCode(
                code=code,
                percentage=10.0,
                valid_from=now,
                valid_until=valid_until,
                used=False
            )
            
            commit()
            
            logger.debug(f"Created discount code: {code}")
            return {"code": code}
            
    except Exception as e:
        logger.error(f"Error creating discount code: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create discount code"
        )

# Reports endpoints
@router.get("/reports/earnings/gender/{gender}", response_model=EarningsReport)
async def get_earnings_by_gender(gender: str):
    """Get earnings report by gender without authentication"""
    try:
        logger.debug(f"Getting earnings by gender {gender} from public endpoint")
        total_earnings = QueryManager.get_earnings_by_gender(gender)
        avg_earnings = QueryManager.get_average_salary_by_gender(gender)
        
        report = EarningsReport(
            group_by="gender",
            filter_value=gender,
            total_earnings=total_earnings,
            average_earnings=avg_earnings
        )
        
        logger.debug(f"Retrieved earnings report for gender {gender}")
        return report
        
    except Exception as e:
        logger.error(f"Error getting earnings by gender: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve earnings report"
        )

@router.get("/reports/earnings/age-group", response_model=EarningsReport)
async def get_earnings_by_age_group(min_age: int, max_age: int):
    """Get earnings report by age group without authentication"""
    try:
        logger.debug(f"Getting earnings by age group {min_age}-{max_age} from public endpoint")
        total_earnings = QueryManager.get_earnings_by_age_group(min_age, max_age)
        avg_earnings = QueryManager.get_average_salary_by_age_group(min_age, max_age)
        
        report = EarningsReport(
            group_by="age_group",
            filter_value=f"{min_age}-{max_age}",
            total_earnings=total_earnings,
            average_earnings=avg_earnings
        )
        
        logger.debug(f"Retrieved earnings report for age group {min_age}-{max_age}")
        return report
        
    except Exception as e:
        logger.error(f"Error getting earnings by age group: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve earnings report"
        )

@router.get("/reports/earnings/postal-code/{postal_code}", response_model=EarningsReport)
async def get_earnings_by_postal_code(postal_code: str):
    """Get earnings report by postal code without authentication"""
    try:
        logger.debug(f"Getting earnings by postal code {postal_code} from public endpoint")
        total_earnings = QueryManager.get_earnings_by_postal_code(postal_code)
        avg_earnings = QueryManager.get_average_salary_by_postal_code(postal_code)
        
        report = EarningsReport(
            group_by="postal_code",
            filter_value=postal_code,
            total_earnings=total_earnings,
            average_earnings=avg_earnings
        )
        
        logger.debug(f"Retrieved earnings report for postal code {postal_code}")
        return report
        
    except Exception as e:
        logger.error(f"Error getting earnings by postal code: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve earnings report"
        )

@router.get("/reports/top-pizzas", response_model=List[TopPizzaInfo])
async def get_top_3_pizzas_past_month():
    """Get top 3 pizzas sold in the past month without authentication"""
    try:
        logger.debug("Getting top 3 pizzas past month from public endpoint")
        top_pizzas = QueryManager.get_top_3_pizzas_past_month()
        
        pizza_list = []
        for item in top_pizzas:
            pizza_info = TopPizzaInfo(
                pizza_id=item['pizza'].id,
                pizza_name=item['pizza'].name,
                total_quantity=item['total_quantity']
            )
            pizza_list.append(pizza_info)
        
        logger.debug(f"Retrieved {len(pizza_list)} top pizzas")
        return pizza_list
        
    except Exception as e:
        logger.error(f"Error getting top pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top pizzas report"
        )

@router.get("/reports/orders/undelivered/customers", response_model=List[OrderInfo])
async def get_undelivered_customer_orders():
    """Get undelivered customer orders without authentication"""
    try:
        logger.debug("Getting undelivered customer orders from public endpoint")
        orders = QueryManager.get_undelivered_customer_orders()
        
        order_list = []
        for order in orders:
            order_info = OrderInfo(
                id=order.id,
                user_id=order.user.id,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                created_at=order.created_at.isoformat() if order.created_at else "",
                postal_code=order.postalCode
            )
            order_list.append(order_info)
        
        logger.debug(f"Retrieved {len(order_list)} undelivered customer orders")
        return order_list
        
    except Exception as e:
        logger.error(f"Error getting undelivered customer orders: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve undelivered customer orders"
        )

@router.get("/reports/orders/undelivered/staff", response_model=List[OrderInfo])
async def get_undelivered_staff_orders():
    """Get undelivered staff orders without authentication"""
    try:
        logger.debug("Getting undelivered staff orders from public endpoint")
        orders = QueryManager.get_undelivered_staff_orders()
        
        order_list = []
        for order in orders:
            order_info = OrderInfo(
                id=order.id,
                user_id=order.user.id,
                status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                created_at=order.created_at.isoformat() if order.created_at else "",
                postal_code=order.postalCode
            )
            order_list.append(order_info)
        
        logger.debug(f"Retrieved {len(order_list)} undelivered staff orders")
        return order_list
        
    except Exception as e:
        logger.error(f"Error getting undelivered staff orders: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve undelivered staff orders"
        )

# User info endpoints (moved from secured.py without authentication)
@router.get("/info/{user_id}", response_model=Union[CustomerSpecificResponse, EmployeeSpecificResponse, DeliveryPersonSpecificResponse])
async def get_user_info(user_id: int):
    """Get user information based on user ID without authentication"""
    try:
        with db_session:
            # Get the user from database
            user = User.get(id=user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check user type and return appropriate response
            if isinstance(user, Customer):
                return CustomerSpecificResponse(
                    message="Customer information",
                    user_type="customer",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    loyalty_points=user.loyalty_points,
                    birthday_order=user.birthday_order
                )
            elif isinstance(user, DeliveryPerson):
                return DeliveryPersonSpecificResponse(
                    message="Delivery person information",
                    user_type="delivery_person",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    status=user.status
                )
            elif isinstance(user, Employee):
                return EmployeeSpecificResponse(
                    message="Employee information",
                    user_type="employee",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unknown user type"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.get("/dashboard/{user_id}", response_model=Union[CustomerSpecificResponse, EmployeeSpecificResponse, DeliveryPersonSpecificResponse])
async def get_user_dashboard(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    dietary_filter: str = "all",
    available_only: bool = False
):
    """Get user dashboard based on user ID without authentication"""
    try:
        logger.debug(f"Getting dashboard for user ID: {user_id}")
        logger.debug(f"Dashboard parameters - page: {page}, page_size: {page_size}, dietary_filter: {dietary_filter}, available_only: {available_only}")

        with db_session:
            # Get the user from database
            user = User.get(id=user_id)
            logger.debug(f"Found user: {user}, type: {type(user)}")
            if not user:
                logger.error(f"User not found in database: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check user type and return appropriate response
            if isinstance(user, Customer):
                logger.debug(f"Processing customer dashboard for user: {user.username}")
                # Get pizzas with prices for customers (with dietary filtering and availability)
                try:
                    # Convert string parameter to DietaryFilter enum
                    logger.debug(f"Converting dietary filter: {dietary_filter}")
                    if dietary_filter == "vegan":
                        filter_enum = DietaryFilter.VEGAN
                    elif dietary_filter == "vegetarian":
                        filter_enum = DietaryFilter.VEGETARIAN
                    elif dietary_filter == "normal":
                        filter_enum = DietaryFilter.NORMAL
                    else:
                        filter_enum = DietaryFilter.ALL

                    logger.debug(f"Using dietary filter enum: {filter_enum}, available_only: {available_only}")

                    # Choose appropriate method based on availability filter
                    if available_only:
                        logger.debug("Calling MenuView.get_available_pizzas_with_prices()")
                        all_pizzas = MenuView.get_available_pizzas_with_prices()
                        logger.debug(f"Retrieved {len(all_pizzas)} available pizzas")
                        # Apply dietary filter manually since get_available_pizzas_with_prices doesn't support filtering
                        if filter_enum != DietaryFilter.ALL:
                            # Filter the results based on dietary type
                            filtered_pizzas = []
                            for pizza in all_pizzas:
                                pizza_entity = Pizza.get(id=pizza['id'])
                                if pizza_entity:
                                    pizza_dietary_type = MenuView.get_pizza_dietary_type(pizza_entity)
                                    if pizza_dietary_type == filter_enum:
                                        filtered_pizzas.append(pizza)
                            all_pizzas = filtered_pizzas
                            logger.debug(f"After dietary filtering: {len(all_pizzas)} pizzas")
                    else:
                        logger.debug("Calling MenuView.get_pizzas_with_prices_and_filters()")
                        all_pizzas = MenuView.get_pizzas_with_prices_and_filters(filter_enum)

                    logger.debug(f"Retrieved {len(all_pizzas)} pizzas with prices (filter: {dietary_filter}, available_only: {available_only})")

                    # Apply pagination to the results
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_pizzas = all_pizzas[start_idx:end_idx]

                    # Convert pizzas to PizzaInfo objects (with full details)
                    pizza_info_list = []
                    for pizza in paginated_pizzas:
                        try:
                            logger.debug(f"Processing pizza: {pizza['name']}")

                            # Convert ingredients to IngredientInfo objects
                            ingredients_info = []
                            for ing in pizza.get('ingredients', []):
                                ingredient_info = IngredientInfo(
                                    name=ing['name'],
                                    price=ing['price'],
                                    type=ing['type']
                                )
                                ingredients_info.append(ingredient_info)

                            pizza_info = PizzaInfo(
                                id=pizza['id'],
                                name=pizza['name'],
                                description=pizza.get('description'),
                                price=pizza['price'],
                                dietary_type=pizza['dietary_type'],
                                stock=pizza['stock'],
                                ingredients=ingredients_info
                            )
                            pizza_info_list.append(pizza_info)
                        except Exception as e:
                            logger.error(f"Error processing pizza {pizza}: {str(e)}")
                            raise

                    # Create pagination info
                    total_count = len(all_pizzas)
                    total_pages = (total_count + page_size - 1) // page_size
                    pagination_info = PaginationInfo(
                        page=page,
                        page_size=page_size,
                        total_count=total_count,
                        total_pages=total_pages,
                        has_next=end_idx < total_count,
                        has_prev=page > 1
                    )

                except Exception as e:
                    logger.error(f"Error in pizzas processing: {str(e)}")
                    raise

                # Get extras (drinks & desserts) for customers
                try:
                    logger.debug("Calling MenuView.get_extras_with_prices()")
                    extras_data = MenuView.get_extras_with_prices()
                    logger.debug(f"Retrieved {len(extras_data)} extras")

                    # Convert extras to ExtraInfo objects
                    extras_info_list = []
                    for extra in extras_data:
                        try:
                            logger.debug(f"Processing extra: {extra['name']}, id: {extra.get('id')}, price: {extra.get('price')}, type: {extra.get('type')}")
                            extra_info = ExtraInfo(
                                id=extra['id'],
                                name=extra['name'],
                                price=extra['price'],
                                type=extra['type']
                            )
                            extras_info_list.append(extra_info)
                        except Exception as e:
                            logger.error(f"Error processing extra {extra}: {str(e)}")
                            logger.error(f"Extra data: {extra}")
                            raise
                except Exception as e:
                    logger.error(f"Error in extras processing: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

                return CustomerSpecificResponse(
                    message="Customer dashboard",
                    user_type="customer",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    loyalty_points=user.loyalty_points,
                    birthday_order=user.birthday_order,
                    available_pizzas=pizza_info_list,
                    pizza_pagination=pagination_info,
                    available_extras=extras_info_list
                )

            elif isinstance(user, Employee):
                # Get all customers for employees
                logger.debug("Getting all customers for employee dashboard")
                customers = list(Customer.select())
                logger.debug(f"Retrieved {len(customers)} customers")
                customer_info_list = [
                    CustomerInfo(
                        id=customer.id,
                        username=customer.username,
                        email=customer.email
                    ) for customer in customers
                ]

                return EmployeeSpecificResponse(
                    message="Employee dashboard",
                    user_type="employee",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    customers=customer_info_list
                )

            elif isinstance(user, DeliveryPerson):
                # Get orders for delivery person
                orders = QueryManager.get_orders_by_user(user.id)
                order_info_list = [
                    OrderInfo(
                        id=order.id,
                        status=order.status,
                        created_at=order.created_at.isoformat() if order.created_at else "",
                        postal_code=order.postalCode
                    ) for order in orders
                ]

                return DeliveryPersonSpecificResponse(
                    message="Delivery person dashboard",
                    user_type="delivery_person",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    status=user.status,
                    orders=order_info_list
                )

            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unknown user type"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_dashboard: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard information"
        )

@router.get("/employee/{user_id}", response_model=EmployeeSpecificResponse)
async def get_employee_info(user_id: int):
    """Get employee information by user ID without authentication"""
    try:
        with db_session:
            # Get the user from database
            user = User.get(id=user_id)
            if not user or not isinstance(user, Employee):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )

        return EmployeeSpecificResponse(
            message="Employee information",
            user_type="employee",
            user_id=user.id,
            username=user.username,
            email=user.email,
            position=user.position,
            salary=user.salary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_employee_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee information"
        )

@router.get("/delivery-person/{user_id}", response_model=DeliveryPersonSpecificResponse)
async def get_delivery_person_info(user_id: int):
    """Get delivery person information by user ID without authentication"""
    try:
        with db_session:
            # Get the user from database
            user = User.get(id=user_id)
            if not user or not isinstance(user, DeliveryPerson):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Delivery person not found"
                )

        return DeliveryPersonSpecificResponse(
            message="Delivery person information",
            user_type="delivery_person",
            user_id=user.id,
            username=user.username,
            email=user.email,
            position=user.position,
            salary=user.salary,
            status=user.status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_delivery_person_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery person information"
        )

@router.get("/pizzas-paginated", response_model=PaginatedPizzaResponse)
async def get_pizzas_paginated(
    page: int = 1,
    page_size: int = 10
):
    """Get pizzas with pagination and prices. Accessible without authentication."""
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )

        # Get paginated pizzas
        pizzas_data = QueryManager.get_pizzas_paginated(page=page, page_size=page_size)

        # Convert pizzas to PizzaInfo objects
        pizza_info_list = []
        for pizza in pizzas_data["pizzas"]:
            # Calculate pizza price using QueryManager
            price = QueryManager.calculate_pizza_price(pizza.id)

            # Get dietary type (default to normal for now)
            dietary_type = "normal"

            pizza_info = PizzaInfo(
                id=pizza.id,
                name=pizza.name,
                description=pizza.description if hasattr(pizza, 'description') else None,
                price=price,
                dietary_type=dietary_type,
                stock=pizza.stock,
                ingredients=[]  # Empty ingredients list for now
            )
            pizza_info_list.append(pizza_info)

        # Create pagination info
        pagination_info = PaginationInfo(**pizzas_data["pagination"])

        return PaginatedPizzaResponse(
            pizzas=pizza_info_list,
            pagination=pagination_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_pizzas_paginated: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve paginated pizzas"
        )

@router.post("/order-multiple-pizzas/{user_id}", response_model=MultiplePizzaOrderResponse, status_code=status.HTTP_201_CREATED)
async def order_multiple_pizzas(
    user_id: int,
    request: MultiplePizzaOrderRequest
):
    """Create an order with multiple pizzas for a specific user without authentication."""
    try:
        logger.debug(f"User {user_id} attempting to order multiple pizzas")
        logger.debug(f"Request data: {request}")

        # Validate pizza quantities
        if not request.pizza_quantities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one pizza must be ordered"
            )

        # Convert PizzaQuantity objects to [pizza_id, quantity] pairs for QueryManager
        pizza_quantities_list = [[pq.pizza_id, pq.quantity] for pq in request.pizza_quantities]

        with db_session:
            # Verify user exists and is a customer
            customer = Customer.get(id=user_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )

            # Create the order using QueryManager
            order = QueryManager.create_multiple_pizza_order(
                user_id=customer.id,
                pizza_quantities=pizza_quantities_list,
                extra_ids=request.extra_ids,
                discount_code=request.discount_code,
                postal_code=request.postal_code
            )

            logger.info(f"Successfully created order {order.id} for customer {customer.username}")

            # Get order confirmation details
            order_details = QueryManager.get_order_confirmation(order.id)
            if not order_details:
                # This shouldn't happen if the order was just created
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve order confirmation"
                )

            # Create response
            response = MultiplePizzaOrderResponse(
                order_id=order.id,
                status=order.status,
                message="Order created successfully",
                total_price=order_details["total_price"],
                items=[
                    OrderItemInfo(
                        type=item["type"],
                        name=item["name"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                        subtotal=item["subtotal"]
                    ) for item in order_details["items"]
                ],
                discount=(
                    DiscountInfo(
                        code=order_details["discount"]["code"],
                        percentage=order_details["discount"].get("percentage", 0.0),
                        amount=order_details["discount"]["amount"]
                    ) if order_details["discount"] else None
                ),
                created_at=order.created_at.isoformat() if order.created_at else "",
                postal_code=order.postalCode
            )

            logger.debug(f"Created response for order {order.id}")
            return response

    except ValueError as e:
        # Handle specific validation errors from QueryManager
        error_message = str(e)
        status_code = status.HTTP_400_BAD_REQUEST

        # Check for specific error types to return appropriate status codes
        if "not found" in error_message.lower():
            if "pizza" in error_message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "extra" in error_message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "user" in error_message.lower():
                status_code = status.HTTP_401_UNAUTHORIZED
        elif "insufficient stock" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "must be positive" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "postal code" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST

        logger.error(f"Validation error in order_multiple_pizzas: {error_message}")
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in order_multiple_pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order due to an internal error"
        )

@router.post("/orders/{order_id}/assign-delivery", response_model=Dict[str, Any])
async def assign_delivery_person_to_order(order_id: int):
    """Assign an available delivery person to an order without authentication"""
    try:
        logger.debug(f"Assigning delivery person to order {order_id}")

        # Use the queryManager function to assign delivery person
        result = QueryManager.assign_delivery_person_to_order(order_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No available delivery persons or order not found"
            )

        logger.info(f"Successfully assigned delivery person {result['delivery_person_id']} to order {order_id}")

        return {
            "message": "Delivery person assigned successfully",
            "order_id": result["order_id"],
            "delivery_person_id": result["delivery_person_id"]
        }

    except ValueError as e:
        logger.error(f"Value error assigning delivery person to order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error assigning delivery person to order {order_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign delivery person to order"
        )