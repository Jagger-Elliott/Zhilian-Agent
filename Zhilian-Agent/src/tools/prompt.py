database_description = """数据库存放着联通公司的用户信息和vip权益信息，执行数据库查询并返回结构化结果，该SQLite数据库包含4个数据表，主要用于管理用户信息、VIP权益数据和广告电话记录。以下是精简后的数据库结构：

        1. VIP权益表 (表名vip_benefits)
        主键: id (INTEGER)

        字段:

        vip_level (TEXT, 非空): VIP等级名称(如青铜/白银/黄金)

        package_type (TEXT, 非空): 套餐类型(如"家庭版单宽200M")

        monthly_fee (REAL, 非空): 月费金额(元)

        contract_duration_months (INTEGER, 非空): 合约期限(月)

        includes_phone_plan (BOOLEAN, 非空): 是否包含电话套餐

        2. 用户表 (表名users)
        主键: id (INTEGER)

        字段:

        name (TEXT, 非空): 用户姓名

        phone (TEXT, 非空): 手机号码(格式181xxxxxxx)

        vip_level (TEXT): VIP等级(当前全为"白银")

        package (TEXT): 当前使用套餐(当前全为"无")

        blacklist (TEXT): 屏蔽号码列表(逗号分隔)

        3. 广告电话表 (表名advertising_calls)
        主键: id (INTEGER)

        字段:

        phone_number (TEXT, 非空): 广告电话号码

        4. 系统序列表 (表名sqlite_sequence)
        字段:

        name (TEXT): 表名

        seq (INTEGER): 当前自增ID值
    """