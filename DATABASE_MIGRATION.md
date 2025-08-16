# 数据库迁移指南

## 问题描述
在添加自定义OpenAI模型功能时，需要在数据库的 `courses` 表中添加 `custom_models` 字段来存储自定义模型配置。

## 错误信息
```
Failed to add custom model: Error adding custom model: 500: Error adding custom model: {"message": "Could not find the 'custom_models' column of 'courses' in the schema cache", "code": "PGRST204", "hint": None, "details": None}
```

## 解决方案

### 步骤1: 运行数据库迁移
1. 登录到你的 Supabase 控制台: https://supabase.com/dashboard
2. 进入你的项目
3. 点击左侧菜单中的 "SQL Editor"
4. 复制并运行以下 SQL 脚本：

```sql
-- Add custom_models column to courses table
-- This migration adds support for storing custom OpenAI API configurations per course

-- Add custom_models column to courses table if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'courses' 
    AND column_name = 'custom_models'
  ) THEN
    ALTER TABLE public.courses 
    ADD COLUMN custom_models JSONB DEFAULT '[]'::jsonb;
    
    -- Add a comment to document the column purpose
    COMMENT ON COLUMN public.courses.custom_models IS 'Stores custom OpenAI API configurations for the course';
    
    -- Create an index for better performance when querying custom models
    CREATE INDEX IF NOT EXISTS idx_courses_custom_models 
    ON public.courses USING gin (custom_models);
    
    RAISE NOTICE 'Successfully added custom_models column to courses table';
  ELSE
    RAISE NOTICE 'Column custom_models already exists in courses table';
  END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses' 
AND column_name = 'custom_models';
```

### 步骤2: 验证迁移成功
运行迁移后，你应该看到类似以下的输出：
```
NOTICE: Successfully added custom_models column to courses table

column_name    | data_type | is_nullable | column_default
custom_models  | jsonb     | YES         | '[]'::jsonb
```

### 步骤3: 重启应用
如果你的应用正在运行，建议重启后端服务以确保数据库架构缓存被更新。

## 或者使用文件方式
你也可以直接运行项目中的迁移文件：
```bash
# 在 Supabase SQL Editor 中运行
cat supabase_setup/add_custom_models_column.sql
```

## 功能说明
添加 `custom_models` 字段后，老师就可以：
1. 在 Admin 面板中为课程添加自定义 OpenAI API key
2. 为自定义模型设置名称（如 "ChatGPT-5"）
3. 学生在聊天界面中可以选择使用这些自定义模型

## 数据结构
`custom_models` 字段存储的 JSON 结构示例：
```json
[
  {
    "name": "ChatGPT-5",
    "api_key": "sk-...",
    "model_type": "openai",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```
