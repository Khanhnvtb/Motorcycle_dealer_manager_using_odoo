# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo.exceptions import ValidationError
import re
from odoo import models, fields, api, _


def format_integer(number):
    number_str = str(number)[::-1]
    result = ''
    for i in range(len(number_str)):
        result += number_str[i]
        if i % 3 == 2:
            result += ','
    return result[::-1]


class MdmUser(models.Model):
    _name = 'mdm.user'

    name = fields.Char(string='Tên người dùng', size=50, required=True)
    dob = fields.Date(string='Sinh nhật', required=True)
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ], 'Giới tính', default='male')
    address = fields.Char(string='Địa chỉ', size=255, required=True)
    phone = fields.Char(string='Số điện thoại', size=10, required=True)
    email = fields.Char(sting='Email', size=50, required=True)
    salary = fields.Integer(string='Lương cơ bản', required=True, default=0)
    invoice_ids = fields.One2many('mdm.import.invoice', 'user_id', string='Danh sách hóa đơn')
    import_receipt_ids = fields.One2many('mdm.import.receipt', 'user_id', string='Danh sách thanh toán nhập hàng')
    export_receipt_ids = fields.One2many('mdm.export.receipt', 'user_id', string='Danh sách thanh toán xuất hàng')
    expense_ids = fields.One2many('mdm.expense', 'user_id', string='Danh sách chi phí')

    @api.constrains('phone')
    def validate_phone(self):
        for rec in self:
            if len(rec.phone) != 10 or rec.phone[0] != '0' or rec.phone[1:].isdigit() == False:
                raise ValidationError('Số điện thoại không đúng định dạng')

    @api.constrains('email')
    def validate_email(self):
        for rec in self:
            if re.match(r"[^@]+@[^@]+\.[^@]+", rec.email):
                pass
            else:
                raise ValidationError('Email không đúng định dạng')

    @api.constrains('salary')
    def validate_salary(self):
        for rec in self:
            if rec.salary < 0:
                raise ValidationError('Lương không được nhỏ hơn 0')

    @api.constrains('dob')
    def validate_dob(self):
        for rec in self:
            if rec.dob >= date.today():
                raise ValidationError('Ngày sinh phải nhỏ hơn ngày hôm nay')


class MdmSupplier(models.Model):
    _name = 'mdm.supplier'

    name = fields.Char(string='Tên nhà cung cấp', size=100, required=True)
    address = fields.Char(string='Địa chỉ', size=100, required=True)
    phone = fields.Char(string='Số điện thoại', size=10, required=True)
    email = fields.Char(string='Email', size=50, required=True)
    transport_price = fields.Integer(string='Phí vận chuyển', required=True, default=0)
    delivery_day = fields.Integer(string='Thời gian vận chuyển', required=True, default=100)
    rating = fields.Float(string='Đánh giá', required=True, default=0)
    import_invoice_ids = fields.One2many('mdm.import.invoice', 'supplier_id', string='Danh sách hóa đơn')

    @api.constrains('phone')
    def validate_phone(self):
        for rec in self:
            if len(rec.phone) != 10 or rec.phone[0] != '0' or rec.phone[1:].isdigit() == False:
                raise ValidationError('Số điện thoại không đúng định dạng')

    @api.constrains('email')
    def validate_email(self):
        for rec in self:
            if re.match(r"[^@]+@[^@]+\.[^@]+", rec.email):
                pass
            else:
                raise ValidationError('Email không đúng định dạng')

    @api.constrains('transport_price')
    def validate_transport_price(self):
        for rec in self:
            if rec.transport_price < 0:
                raise ValidationError('Phí vận chuyển không được nhỏ hơn 0')


class MdmImportInvoice(models.Model):
    _name = 'mdm.import.invoice'

    time = fields.Datetime(string='Thời gian nhập', default=datetime.now())
    total = fields.Integer(string='Tổng tiền', size=None)
    payment = fields.Integer(string='Tiền đã thanh toán', size=None, required=True, default=0)
    debt_term = fields.Date(string='Ngày hết hạn', required=True)
    user_id = fields.Many2one('mdm.user')
    supplier_id = fields.Many2one('mdm.supplier', required=True)
    import_invoice_ids = fields.One2many('mdm.import.motor', 'import_invoice_id', string='Danh sách xe nhập')
    import_receipt_ids = fields.One2many('mdm.import.receipt', 'import_invoice_id', string='Danh sách thanh toán nhập hàng')

    @api.model
    def create(self, vals):
        import_invoice = super().create(vals)

        import_motors = import_invoice.import_invoice_ids

        for record in import_motors:
            motor = self.env['mdm.motor'].search([('id', '=', record.motor_id.id)])
            motor.quantity += record.quantity
            record.sum_import_price = motor.import_price * record.quantity

        if import_invoice.payment > 0:
            self.env['mdm.import.receipt'].create({
                'import_invoice_id': import_invoice.id,
                'money': import_invoice.payment,
                'note': 'Thanh toán khi nhập hàng'
            })

        return import_invoice

    @api.constrains('payment')
    def validate_payment(self):
        for rec in self:
            if rec.payment < 0:
                raise ValidationError('Số tiền đã thanh toán không thể nhỏ hơn 0')
            elif rec.payment > rec.total:
                raise ValidationError('Số tiền đã thanh toán không thể lớn hơn tổng số tiền')

    @api.constrains('debt_term')
    def validate_debt_term(self):
        for rec in self:
            if rec.debt_term <= date.today():
                raise ValidationError('Ngày hết hạn phải lớn hơn ngày hôm nay')

    @api.constrains('import_invoice_ids')
    def validate_import_invoice_ids(self):
        for rec in self:
            if len(rec.import_invoice_ids) == 0:
                raise ValidationError('Danh sách nhập xe không được để trống')

    @api.onchange('import_invoice_ids')
    def onchange_import_invoice_ids(self):
        self.total = 0
        for record in self.import_invoice_ids:
            motor = self.env['mdm.motor'].search([('id', '=', record.motor_id.id)])
            record.sum_import_price = motor.import_price * record.quantity
            self.total += record.sum_import_price

    def add_import_receipt(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import receipt'),
            'view_mode': 'tree',
            'res_model': 'mdm.import.receipt',
            'target': 'current',
            'domain': [('import_invoice_id', '=', self.id)],
            'context': {
                'default_import_invoice_id': self.id
            }
        }


class MdmMotor(models.Model):
    _name = 'mdm.motor'

    name = fields.Char(string='Tên xe', size=100, unique=True, required=True)
    brand = fields.Char(string='Thương hiệu', size=100, required=True)
    description = fields.Char(string='Mô tả', size=1000, required=True)
    quantity = fields.Integer(string='Số lượng', required=True, default=0)
    import_price = fields.Integer(string='Giá nhập', required=True)
    export_price = fields.Integer(string='Giá bán', required=True)
    import_motor_ids = fields.One2many('mdm.import.motor', 'motor_id', string='Danh sách xe nhập')
    export_motor_ids = fields.One2many('mdm.export.motor', 'motor_id', string='Danh sách xe xuất')

    @api.constrains('quantity')
    def validate_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError('Số lượng không được nhỏ hơn 0')

    @api.constrains('import_price')
    def validate_import_price(self):
        for rec in self:
            if rec.import_price <= 0:
                raise ValidationError('Giá nhập phải lớn hơn 0')

    @api.constrains('export_price')
    def validate_export_price(self):
        for rec in self:
            if rec.export_price <= rec.import_price:
                raise ValidationError('Giá xuất phải lớn hơn giá nhập')


class MdmImportReceipt(models.Model):
    _name = 'mdm.import.receipt'

    user_id = fields.Many2one('mdm.user')
    import_invoice_id = fields.Many2one('mdm.import.invoice', required=True)
    time = fields.Datetime(string='Thời gian', default=datetime.now())
    money = fields.Integer(string='Số tiền thanh toán', size=None, required=True)
    note = fields.Char(string='Ghi chú', size=100)

    @api.model
    def create(self, vals):
        import_receipt = super().create(vals)
        import_invoice = self.env['mdm.import.invoice'].search([('id', '=', import_receipt.import_invoice_id.id)])
        import_invoice.payment += import_receipt.money
        return import_receipt

    @api.constrains('money')
    def validate_money(self):
        for rec in self:
            if rec.money <= 0:
                raise ValidationError('Số tiền thanh toán phải lớn hơn 0')
            elif rec.money > rec.import_invoice_id.total - rec.import_invoice_id.payment:
                raise ValidationError(
                    f'Bạn đã trả quá số tiền cho tổng hoá đơn, số tiền còn lại cần phải trả là {format_integer(rec.import_invoice_id.total - rec.import_invoice_id.payment)}')


class MdmImportMotor(models.Model):
    _name = 'mdm.import.motor'

    import_invoice_id = fields.Many2one('mdm.import.invoice', required=True)
    motor_id = fields.Many2one('mdm.motor', required=True, string='Xe máy')
    quantity = fields.Integer(string='Số lượng xe nhập', required=True, default=1)
    sum_import_price = fields.Integer(string='Thành tiền')

    @api.constrains('quantity')
    def validate_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError('Số lượng xe nhập phải lớn hơn 0')


class MdmStore(models.Model):
    _name = 'mdm.store'

    name = fields.Char(string='Tên cửa hàng', size=100, unique=True, required=True)
    owner = fields.Char(string='Tên chủ sở hữu', size=50, required=True)
    address = fields.Char(string='Địa chỉ cửa hàng', size=100, required=True)
    phone = fields.Char(string='Số điện thoại', size=10, required=True)
    email = fields.Char(string='Email', size=50, required=True)
    export_invoice_ids = fields.One2many('mdm.export.invoice', 'store_id', string='Danh sách xe xuất')

    @api.constrains('phone')
    def validate_phone(self):
        for rec in self:
            if len(rec.phone) != 10 or rec.phone[0] != '0' or rec.phone[1:].isdigit() == False:
                raise ValidationError('Số điện thoại không đúng định dạng')

    @api.constrains('email')
    def validate_email(self):
        for rec in self:
            if re.match(r"[^@]+@[^@]+\.[^@]+", rec.email):
                pass
            else:
                raise ValidationError('Email không đúng định dạng')


class MdmExportInvoice(models.Model):
    _name = 'mdm.export.invoice'

    time = fields.Datetime(string='Thời gian', default=datetime.now())
    total = fields.Integer(string='Tổng tiền', size=None)
    payment = fields.Integer(string='Tiền đã thanh toán', size=None, required=True)
    debt_term = fields.Date(string='Ngày hết hạn', required=True)
    user_id = fields.Many2one('mdm.user')
    store_id = fields.Many2one('mdm.store', required=True)
    export_invoice_ids = fields.One2many('mdm.export.motor', 'export_invoice_id', string='Danh sách xe xuất')
    export_receipt_ids = fields.One2many('mdm.export.receipt', 'export_invoice_id', string='Danh sách thanh toán xuất hàng')

    @api.model
    def create(self, vals):
        export_invoice = super().create(vals)

        export_motors = export_invoice.export_invoice_ids

        for record in export_motors:
            motor = self.env['mdm.motor'].search([('id', '=', record.motor_id.id)])
            motor.quantity -= record.quantity
            record.sum_export_price = motor.export_price * record.quantity
            
        if export_invoice.payment > 0:
            self.env['mdm.export.receipt'].create({
                'export_invoice_id': export_invoice.id,
                'money': export_invoice.payment,
                'note': 'Thanh toán khi xuất hàng'
            })

        return export_invoice

    @api.constrains('payment')
    def validate_payment(self):
        for rec in self:
            if rec.payment < 0:
                raise ValidationError('Số tiền đã thanh toán không thể nhỏ hơn 0')
            elif rec.payment > rec.total:
                raise ValidationError('Số tiền đã thanh toán không thể lớn hơn tổng số tiền')

    @api.constrains('debt_term')
    def validate_debt_term(self):
        for rec in self:
            if rec.debt_term <= date.today():
                raise ValidationError('Ngày hết hạn phải lớn hơn ngày hôm nay')

    @api.constrains('export_invoice_ids')
    def validate_export_invoice_ids(self):
        for rec in self:
            if len(rec.export_invoice_ids) == 0:
                raise ValidationError('Danh sách xuất xe không được để trống')

    @api.onchange('export_invoice_ids')
    def onchange_export_invoice_ids(self):
        self.total = 0
        for record in self.export_invoice_ids:
            motor = self.env['mdm.motor'].search([('id', '=', record.motor_id.id)])
            record.sum_export_price = motor.export_price * record.quantity
            self.total += record.sum_export_price

    def add_export_receipt(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export receipt'),
            'view_mode': 'tree',
            'res_model': 'mdm.export.receipt',
            'target': 'current',
            'domain': [('export_invoice_id', '=', self.id)],
            'context': {
                'default_export_invoice_id': self.id
            }
        }


class MdmExportMotor(models.Model):
    _name = 'mdm.export.motor'

    export_invoice_id = fields.Many2one('mdm.export.invoice', required=True)
    motor_id = fields.Many2one('mdm.motor', required=True, string="Xe máy")
    quantity = fields.Integer(string='Số lượng xe xuất', required=True, default=1)
    sum_export_price = fields.Integer(string="Thành tiền")

    @api.constrains('quantity')
    def validate_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError('Số lượng xuất phải lơn hơn 0')
            elif rec.quantity > rec.motor_id.quantity:
                raise ValidationError(
                    f'Số lượng trong kho không đủ, xe {rec.motor_id.name} còn lại {rec.motor_id.quantity} xe')


class MdmExportReceipt(models.Model):
    _name = 'mdm.export.receipt'

    user_id = fields.Many2one('mdm.user')
    export_invoice_id = fields.Many2one('mdm.export.invoice', required=True)
    time = fields.Datetime(string='Thời gian', default=datetime.now())
    money = fields.Integer(string='Số tiền thanh toán', size=None, required=True)
    note = fields.Char(string='Ghi chú', size=100)

    @api.model
    def create(self, vals):
        export_receipt = super().create(vals)
        export_invoice = self.env['mdm.export.invoice'].search([('id', '=', export_receipt.export_invoice_id.id)])
        export_invoice.payment += export_receipt.money
        return export_receipt

    @api.constrains('money')
    def validate_money(self):
        for rec in self:
            if rec.money <= 0:
                raise ValidationError('Số tiền thanh toán phải lớn hơn 0')
            elif rec.money > rec.export_invoice_id.total - rec.export_invoice_id.payment:
                raise ValidationError(
                    f'Bạn đã trả quá số tiền cho tổng hoá đơn, số tiền còn lại cần phải trả là {format_integer(rec.export_invoice_id.total - rec.export_invoice_id.payment)}', )


class MdmExpense(models.Model):
    _name = 'mdm.expense'

    user_id = fields.Many2one('mdm.user')
    time = fields.Datetime(string='Thời gian', default=datetime.now())
    money = fields.Integer(string='Thành tiền', size=None, required=True)
    type = fields.Char(string='Loại chi phí', size=100, required=True)
    note = fields.Char(string='Ghi chú', size=100)

    @api.constrains('money')
    def validate_import_price(self):
        for rec in self:
            if rec.money < 0:
                raise ValidationError('Số tiền không được nhỏ hơn 0')
