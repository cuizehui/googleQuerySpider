import threading
import time

exitFlag = 0


class myThread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, name, shopInfo):
        threading.Thread.__init__(self)
        self.shopInfo = shopInfo
        self.name = name

    def run(self):
        self.print_time()

    def print_time(self):
        print("Starting %s " % self.name)
        print("shopInfo  %s  Exiting" % self.shopInfo.shop_name)
        print("Exiting %s " % self.name)


print
"Exiting Main Thread"


class ShopInfo:
    number: str
    keyWord: str
    spider_file: str
    shop_name: str
    url: str
    country: str
    icon: str

    def __init__(self) -> None:
        super().__init__()
        self.number = ""
        self.keyWord = ""
        self.spider_file = ""
        self.shop_name = ""
        self.url = ""
        self.icon = ""
        pass


def main():
    # 创建新线程

    shopInfo = ShopInfo()
    shopInfo.shop_name = "shop 111"
    thread1 = myThread("thread 1", shopInfo)
    thread1.start()
    shopInfo = ShopInfo()
    shopInfo.shop_name = "shop 222"
    thread2 = myThread("thread 2", shopInfo)
    thread2.start()

    # 开启线程

    pass


if __name__ == '__main__':
    main()
