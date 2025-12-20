-- 将默认标签转移给当前用户
-- 替换 'YOUR_OPENID' 为你的真实 openid

-- 方法1：直接更新所有默认标签的 owner_openid
UPDATE wardrobe_categories 
SET owner_openid = 'ofgZF1_qrt740vKblnPF4coV0so0'  -- 替换为你的 openid
WHERE owner_openid = 'default';

-- 查看结果
SELECT id, owner_openid, name, sort_order FROM wardrobe_categories;
