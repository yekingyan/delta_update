# coding=utf-8
from functools import wraps


class DeltaUpdateException(Exception):
    pass


class _DeltaUpdate(object):
    def __init__(self):
        self.m_listItem = []
        self.m_bCollect = False

    def CollectChangeItem(self, item):
        def _BeforeCollect():
            if not self.m_bCollect:
                raise DeltaUpdateException()
            if item in self.m_listItem:
                raise DeltaUpdateException()
            self.BeforeCollectChangeItem(item)

        def _AfterCollect():
            self.AfterCollectChangeItem(item)

        def Decorate(func):
            @wraps(func)
            def Wrapper(*args, **kwargs):
                bCollect = True
                try:
                    _BeforeCollect()
                except DeltaUpdateException:
                    bCollect = False
                res = func(*args, **kwargs)
                if bCollect:
                    self.m_listItem.append(item)
                    _AfterCollect()
                return res

            return Wrapper

        return Decorate

    def BeforeCollectChangeItem(self, item):
        pass

    def AfterCollectChangeItem(self, item):
        pass

    def RegisterUpdateChange(self, *args, **kwargs):
        def _BeforeUpdateChange():
            self.m_listItem = []
            self.BeforeUpdateChange(*args, **kwargs)

        def _AfterUpdateChange():
            self.m_bCollect = False
            self.AfterUpdateChange(*args, **kwargs)

        def Decorate(func):
            @wraps(func)
            def Wrapper(*ar, **kw):
                bUpdate = True
                try:
                    self.m_bCollect = True
                    _BeforeUpdateChange()
                except DeltaUpdateException:
                    self.m_bCollect = False
                    bUpdate = False
                res = func(*ar, **kw)
                if bUpdate:
                    self.UpdateChange(*args, **kwargs)
                    _AfterUpdateChange()
                return res

            return Wrapper

        return Decorate

    def BeforeUpdateChange(self, *args, **kwargs):
        pass

    def UpdateChange(self, *args, **kwargs):
        raise NotImplementedError

    def AfterUpdateChange(self, *args, **kwargs):
        pass


class DeltaUpdate(_DeltaUpdate):
    def CollectChangeItem(self, item):
        """
        收集发生变化的元素
        使用装饰器 @self.CollectChangeItem("a")
        当被装饰函数被调用时，即元素a发生了改变，会被收集。
        前提是BeforeCollectChangeItem不拦截这次收集
        """
        return super(DeltaUpdate, self).CollectChangeItem(item)

    def BeforeCollectChangeItem(self, item):
        """
        勾子，收集元素之前
        可通过 raise DeltaUpdateException()，中止此次收集
        """
        pass

    def AfterCollectChangeItem(self, item):
        """勾子，成功收集元素之后"""
        pass

    def RegisterUpdateChange(self, *args, **kwargs):
        """
        注册同步改变
        使用装饰器 @self.RegisterUpdateChange()
        如被装饰函数m,当函数m被调用，函数m的子函数会收集变化元素
        函数m执行完毕，会调用UpdateChange
        """
        return super(DeltaUpdate, self).RegisterUpdateChange(*args, **kwargs)

    def BeforeUpdateChange(self, *args, **kwargs):
        """
        勾子，UpdateChange之前
        可通过 raise DeltaUpdateException()，中止此次UpdateChange
        """
        pass

    def UpdateChange(self, *args, **kwargs):
        """
        自定的同步动作
        可通过self.m_listItem查看，收集到的元素，决定同步的内容
        """
        raise NotImplementedError

    def AfterUpdateChange(self, *args, **kwargs):
        """勾子，触发UpdateChange之后"""
        pass
