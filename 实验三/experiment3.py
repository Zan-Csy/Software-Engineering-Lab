"""
软件工程实验三：面向对象的系统建模
语言：Python
包含题目：A1-1, A1-2, A1-3, A1-4 
"""

from datetime import date
from abc import ABC, abstractmethod


# ==========================================
# 题目 A1-1：良种马类 (Thoroughbred)
# ==========================================
class Thoroughbred:
    def __init__(self, birthyear: int, father=None, mother=None):
        self.__birthyear = birthyear
        self.__father = father
        self.__mother = mother

    def get_current_age(self, current_year: int) -> int:
        return current_year - self.__birthyear

    def get_father(self):
        return self.__father

    def get_mother(self):
        return self.__mother


# ==========================================
# 题目 A1-2：学院、建筑与课程关系
# 核心考察点：聚合(Aggregation)、组合(Composition)、约束(Constraint)
# ==========================================
class Building:
    def __init__(self, name: str):
        self.name = name


class Course:
    def __init__(self, name: str, building: Building):
        # 约束性体现：Course 一定在某个 Building 中进行
        if building is None:
            raise ValueError("约束冲突：Course 必须指定在某个 Building 中进行！")
        self.name = name
        self.building = building


class College:
    def __init__(self, name: str):
        self.name = name
        self.buildings = []  # 聚合关系：建筑构成了学院，但建筑可脱离学院存在
        self.courses = []    # 组合关系：课程依附于学院

    def add_building(self, building: Building):
        self.buildings.append(building)

    def create_course(self, course_name: str, building: Building):
        course = Course(course_name, building)
        self.courses.append(course)
        return course


# ==========================================
# 题目 A1-3：高校组织架构与多重性
# 核心考察点：1对多、多重性约束 (1..*、1..3、1..5)
# ==========================================
class Subject:
    def __init__(self, name: str):
        self.name = name


class Instructor:
    def __init__(self, name: str):
        self.name = name
        self.teaching_subjects = []  # 约束：教授 1-3 门课程

    def assign_subject(self, subject: Subject):
        if len(self.teaching_subjects) >= 3:
            raise ValueError(f"约束冲突：教师 {self.name} 最多只能教授 3 门课程！")
        self.teaching_subjects.append(subject)


class Student:
    def __init__(self, name: str):
        self.name = name
        self.learning_subjects = []  # 约束：参加 1-5 门课程学习

    def enroll_subject(self, subject: Subject):
        if len(self.learning_subjects) >= 5:
            raise ValueError(f"约束冲突：学生 {self.name} 最多只能参加 5 门课程！")
        self.learning_subjects.append(subject)


class Department:
    def __init__(self, name: str):
        self.name = name
        self.instructors = []  # 每个系至少拥有 1 位教师 (1..*)
        self.subjects = []     # 每个系提供至少 1 门课程 (1..*)

    def add_instructor(self, instructor: Instructor):
        self.instructors.append(instructor)

    def add_subject(self, subject: Subject):
        self.subjects.append(subject)


class School:
    def __init__(self, name: str):
        self.name = name
        self.departments = []  # 学院由 1 到多个系构成 (1..*)
        self.students = []     # 学院拥有 0 到多名学生 (0..*)

    def add_department(self, department: Department):
        self.departments.append(department)

    def add_student(self, student: Student):
        self.students.append(student)


# ==========================================
# 题目 A1-4：简化的网上购物系统
# ==========================================
class Product:
    def __init__(self, title: str, weight: float, description: str, unit_price: float):
        self.__title = title
        self.__weight = weight
        self.__description = description
        self.__unit_price = unit_price

    def get_price_for_quantity(self, quantity: int) -> float:
        return self.__unit_price * quantity

    def get_weight(self) -> float:
        return self.__weight


class OrderDetail:
    def __init__(self, quantity: int, product: Product):
        self.__quantity = quantity
        self.__product = product

    def calculate_sub_total(self) -> float:
        return self.__product.get_price_for_quantity(self.__quantity)

    def calculate_weight(self) -> float:
        return self.__product.get_weight() * self.__quantity


class Payment(ABC):
    def __init__(self, amount: float):
        self._amount = amount

    @abstractmethod
    def pay(self):
        pass


class Credit(Payment):
    def __init__(self, amount: float, number: str, card_type: str, expired_date: str):
        super().__init__(amount)
        self.__number = number
        self.__type = card_type
        self.__expired_date = expired_date

    def pay(self):
        print(f"使用信用卡 {self.__number} 完成支付，金额：{self._amount} 元")


class Cash(Payment):
    def __init__(self, amount: float, cash_tendered: float):
        super().__init__(amount)
        self.__cash_tendered = cash_tendered

    def pay(self):
        print(f"现金支付成功，实收 {self.__cash_tendered} 元，找零 {self.__cash_tendered - self._amount} 元")


class WireTransfer(Payment):
    def __init__(self, amount: float, bank_id: str, bank_name: str):
        super().__init__(amount)
        self.__bank_id = bank_id
        self.__bank_name = bank_name

    def pay(self):
        print(f"在线转账成功：{self.__bank_name}({self.__bank_id})，金额：{self._amount} 元")


class AliPay(Payment):
    def __init__(self, amount: float, number: str):
        super().__init__(amount)
        self.__number = number

    def pay(self):
        print(f"支付宝账号 {self.__number} 成功支付 {self._amount} 元")


class WeixinPay(Payment):
    def __init__(self, amount: float, number: str):
        super().__init__(amount)
        self.__number = number

    def pay(self):
        print(f"微信账号 {self.__number} 成功支付 {self._amount} 元")


class Order:
    def __init__(self, create_date: str):
        self.__create_date = create_date
        self.__status = "CREATE"
        self.__order_details = []
        self.__payment = None

    def add_order_detail(self, detail: OrderDetail):
        self.__order_details.append(detail)

    def set_payment(self, payment: Payment):
        self.__payment = payment
        self.__status = "PAID"
        payment.pay()

    def calculate_total_amount(self) -> float:
        return sum(d.calculate_sub_total() for d in self.__order_details)

    def calculate_total_weight(self) -> float:
        return sum(d.calculate_weight() for d in self.__order_details)


class Customer:
    def __init__(self, name: str, contact: str, delivery_address: str):
        self.__name = name
        self.__contact = contact
        self.__delivery_address = delivery_address
        self.__active = True
        self.__orders = []

    def add_order(self, order: Order):
        self.__orders.append(order)


# ==========================================
# 完整测试执行
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("      软件工程实验三 综合验证输出")
    print("=" * 50)

    # 1. A1-1 测试
    horse = Thoroughbred(birthyear=2018)
    print(f"\n[A1-1 良种马测试]: 2018年出生的马在 2024 年的年龄为 {horse.get_current_age(2024)} 岁")

    # 2. A1-2 测试
    college = College("信息工程学院")
    bldg = Building("科技实验楼")
    college.add_building(bldg)
    course = college.create_course("面向对象系统建模", bldg)
    print(f"[A1-2 聚合组合测试]: {college.name} 包含课程 [{course.name}]，授课地点为 [{course.building.name}]")

    # 3. A1-3 测试
    school = School("大学信息学部")
    dept = Department("软件工程系")
    teacher = Instructor("王老师")
    sub1 = Subject("UML建模")
    teacher.assign_subject(sub1)
    dept.add_instructor(teacher)
    dept.add_subject(sub1)
    school.add_department(dept)

    student = Student("李四")
    student.enroll_subject(sub1)
    school.add_student(student)
    print("[A1-3 高校架构测试]: ")
    print(f"{school.name} -> {dept.name} -> 教师 {teacher.name} 教授 [{teacher.teaching_subjects[0].name}]")
    print(f"学生 {student.name} 选修了 {len(student.learning_subjects)} 门课")

    # 4. A1-4 测试
    print(f"[A1-4 网上购物测试]:")
    customer = Customer("张三", "13800138000", "北京市海淀区")
    prod = Product("红富士苹果", 0.2, "新鲜水果", 5.0)
    order = Order(str(date.today()))
    order.add_order_detail(OrderDetail(quantity=4, product=prod))
    customer.add_order(order)

    print(f"-> 订单总金额: {order.calculate_total_amount()} 元, 总重量: {order.calculate_total_weight()} kg")
    pay_method = WeixinPay(order.calculate_total_amount(), "wx_123456")
    order.set_payment(pay_method)
