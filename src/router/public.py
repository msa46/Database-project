from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pony.orm import db_session
import logging
import traceback

from ..database.models import ExtraType, IngredientType, DeliveryStatus, OrderStatus, DiscountCode
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