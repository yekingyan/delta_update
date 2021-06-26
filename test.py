# coding=utf-8
import unittest

from delta_update import DeltaUpdate, DeltaUpdateException


class RightResponse(Exception):
    pass


class TestDu(DeltaUpdate):
    def UpdateChange(self, *args, **kwargs):
        pass


du = TestDu()


class TestDeltaUpdate(unittest.TestCase):
    def setUp(self):
        global du
        du = TestDu()

    def testCollectedFun(self):
        """被收集函数"""
        # 位置参数
        @du.CollectChangeItem("a")
        def a(i, j):
            self.assertEqual(1, i)
            self.assertEqual(2, j)
        a(1, 2)

        # 关键字参数
        @du.CollectChangeItem("a")
        def b(i=0, j=0):
            self.assertEqual(1, i)
            self.assertEqual(2, j)
        b(i=1, j=2)

        # 混合参数
        def c(i, j=0, k=0):
            self.assertEqual(1, i)
            self.assertEqual(0, j)
            self.assertEqual(2, k)
        c(1, k=2)

    def testCollectChangeItem(self):
        @du.CollectChangeItem("a")
        def a(): pass

        @du.CollectChangeItem("b")
        def b(): pass

        # 没有开启收集的收集行为是无效的
        def m():
            a()
            self.assertEqual([], du.m_listItem)
        m()

        # 在注册了收集行为的函数中进行
        @du.RegisterUpdateChange()
        def m1():
            self.assertEqual([], du.m_listItem)  # 开始时是空列表
            a()
            self.assertEqual(["a"], du.m_listItem)
        m1()

        # 重复收集
        @du.RegisterUpdateChange()
        def m2():
            self.assertEqual([], du.m_listItem)
            a()
            self.assertEqual(["a"], du.m_listItem)
            b()
            self.assertEqual(["a", "b"], du.m_listItem)
            a()
            self.assertEqual(["a", "b"], du.m_listItem)
        m2()

    def testBeforeCollectChangeItem(self):
        # 正常触发before hook
        def hook1(item):
            self.assertEqual("a", item, u"勾子正常触发元素不正确")
        du.BeforeCollectChangeItem = hook1

        @du.CollectChangeItem("a")
        def a(): pass

        @du.RegisterUpdateChange()
        def m1():
            a()
            self.assertEqual(["a"], du.m_listItem, u"没有勾子拦截，收集元素不正确")
        m1()

        # before hook 拦截
        def hook2(item):
            if item == "a":
                raise DeltaUpdateException(item)
        du.BeforeCollectChangeItem = hook2

        @du.CollectChangeItem("b")
        def b(): pass

        @du.RegisterUpdateChange()
        def m2():
            a()
            self.assertEqual([], du.m_listItem, u"勾子拦截了收集，结果应为空")
            b()
            self.assertEqual(["b"], du.m_listItem, u"勾子拦截了a，只有b")
        m2()

    def testAfterCollectChangeItem(self):
        # after hook 未拦截，正常触发
        def afHook1(item):
            raise RightResponse(item)
        du.AfterCollectChangeItem = afHook1

        @du.CollectChangeItem("a")
        def a(): pass

        @du.RegisterUpdateChange()
        def m1():
            a()

        with self.assertRaises(RightResponse):
            m1()

        # after hook 拦截，就不会有触发
        def bfHook2(item):
            raise DeltaUpdateException(item)

        def afHook2(item):
            raise Exception("不应触发hook2 {}".format(item))

        du.BeforeCollectChangeItem = bfHook2
        du.AfterCollectChangeItem = afHook2

        @du.RegisterUpdateChange()
        def m2():
            a()
        m2()

    def testRegisterUpdateChange(self):
        # 未注册是收集不到元素的
        @du.CollectChangeItem("a")
        def a(): pass

        def m1():
            a()
        m1()
        self.assertEqual([], du.m_listItem, u"未注册的调用却收集到了元素")

        # 注册后的调用可以收集元素
        @du.RegisterUpdateChange()
        def m2():
            a()
        m2()
        self.assertEqual(["a"], du.m_listItem, u"注册的调用却收集不到元素")

    def testBeforeUpdateChange(self):
        # 正常触发before hook
        def hook1(i, j, k=0):
            self.assertEqual((1, 2, 3), (i, j, k), u"传参错误")
            raise RightResponse()
        du.BeforeUpdateChange = hook1

        @du.CollectChangeItem("a")
        def a(): pass

        @du.RegisterUpdateChange(1, 2, k=3)
        def m1():
            a()

        with self.assertRaises(RightResponse):
            m1()

        # before hook 拦截
        def hook2():
            raise DeltaUpdateException()
        du.BeforeUpdateChange = hook2

        @du.CollectChangeItem("b")
        def b(): pass

        @du.RegisterUpdateChange()
        def m2():
            a()
            b()
            self.assertEqual([], du.m_listItem, u"勾子拦截了收集，结果应为空")
        m2()

    def testUpdateChange(self):
        def UpdateChange(*args, **kwargs):
            self.assertEqual((1, 2), args, u"位置参数错误")
            self.assertEqual(3, kwargs["k"], u"关键字参数错误")
            self.assertEqual(["a", "m"], du.m_listItem, u"收集元素错误")
        du.UpdateChange = UpdateChange

        @du.CollectChangeItem("a")
        def a(): pass

        @du.RegisterUpdateChange(1, 2, k=3)
        @du.CollectChangeItem("m")
        def m1():
            a()
        m1()

    def testAfterUpdateChange(self):
        # after hook 未拦截，正常触发
        def afHook1(i):
            self.assertEqual(1, i, "参数错误")
            raise RightResponse()
        du.AfterUpdateChange = afHook1

        @du.CollectChangeItem("a")
        def a(): pass

        @du.RegisterUpdateChange(1)
        def m1():
            a()

        with self.assertRaises(RightResponse):
            m1()

        # after hook 拦截，就不会有触发
        def bfHook2():
            raise DeltaUpdateException()

        def afHook2():
            raise Exception("不应触发hook2")

        du.BeforeUpdateChange = bfHook2
        du.AfterUpdateChange = afHook2

        @du.RegisterUpdateChange()
        def m2():
            a()
        m2()
