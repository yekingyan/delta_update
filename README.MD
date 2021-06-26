# 增量更新

## 一、快速开始

```python
# coding=utf-8

# 被观察的数据，这里被修改过的数据需要同步到别的地方
dictData = {
    "yuanbao": 100,
    "stock": 5,
    "point": 10,
    "other": 0,
}

# 1.1 继承DeltaUpdate类，并覆写UpdateChange方法
from delta_update import DeltaUpdate

class MyDeltaUpdate(DeltaUpdate):
    def UpdateChange(self):
        if not self.m_listItem:
            return
        # 在调用一次order接口后，yuanbao、stock、point的数据改变了
        # 这正是我们需要同步的增量更新的数据
        dictPartialData = {k: v for k, v in dictData.iteritems() if k in self.m_listItem}
        SyncRpc(dictPartialData)

myDu = MyDeltaUpdate()

# 1.2 注册更新改变函数
"""
所谓更新改变函数，即当这个函数被调用的，会做一些改变被观察的数据操作
一般是业务逻辑接口，比如下订单接口会扣库存、扣元宝
"""


@myDu.RegisterUpdateChange()
def order():
    yuanbo()
    stock()


# 1.3 收集变更元素
"""
在某一些函数方法调用，特定的数据会被改变，需这个变更是我们感兴趣的
"""


@myDu.CollectChangeItem("yuanbao")
@myDu.CollectChangeItem("point")
def yuanbo():
    dictData["yuanbao"] -= 1
    dictData["point"] += 1


@myDu.CollectChangeItem("stock")
def stock():
    dictData["stock"] -= 1

order()
```

## 二、生命周期

被@DeltaUpdate.RegisterUpdateChange()装饰的函数m  
当函数m被调用时，便是生命周期的开始

### 2.1 BeforeUpdateChange

BeforeUpdateChange阶段，在逻辑函数m的运行之前

* 收集开关会被打开，self.m_bCollect = True
* 收集元素列表初始化置空， self.m_listItem = []

在这个勾子里面可以中断所有的收集行为

* 当raise DeltaUpdateException之后，生命周期就结束了
* 但主函数m仍然会执行

### 2.2 收集阶段

收集阶段，在逻辑函数m的运行期间  
每一个被@DeltaUpdate.CollectChangeItem()装饰的函数被调用，即是一个收集行为

### 2.2.1 BeforeCollectChangeItem

收集元素之前
raise DeltaUpdateException 可打断单个单个收集行为

### 2.2.2 AfterCollectChangeItem

成功收集元素之后

### 2.3 UpdateChange

UpdateChange阶段，所有的元素收集完成于self.m_listItem  
此时会调用需要覆写的UpdateChange方法，在这里可以收集到增量更新的元素，做增量同步

### 2.4 AfterUpdateChange

AfterUpdateChange阶段

## 三、其它

### 3.1 例子

```python
from partial_update import DeltaUpdate
class Du(DeltaUpdate):
    def __init__(self):
        self.m_szPlayerID = None
        super(Du, self).__init__()

    def SetPlayerID(self, szPlayerID):
        self.m_szPlayerID = szPlayerID

    def BeforeUpdateChange(self, bSync2Gac=True, bSync2Gas=True):
        self.SetPlayerID(None)

    def UpdateChange(self, bSync2Gac=True, bSync2Gas=True):
        print ("listItem", self.m_listItem)
        print ("bSync2Gac, bSync2Gas: {}".format((bSync2Gac, bSync2Gas)))
        print ("PlayerID", self.m_szPlayerID)

du = Du()

@du.CollectChangeItem("a")
def a(i, ii=1):
    print ("a", i, ii)

@du.CollectChangeItem("b")
def b(j):
    print ("b", j)

@du.RegisterUpdateChange(bSync2Gac=False)
def m1():
    a(1, ii=11)
    b(2)
    a(1)
    du.SetPlayerID("asdfasdf")

m1()
print "-"*50

@du.CollectChangeItem("c")
def c(*x, **y):
    print ("c", x, y)

@du.RegisterUpdateChange(bSync2Gas=False)
def m2():
    c(3, a=33, b=333)

m2()
```
