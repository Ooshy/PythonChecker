#prog3.py
#Victoria Parrish
#Project 3
from random import*
import math

def relativePrime(n):
    if(n%2 == 0):
        return False
    else:
        return True
def main():
    print("Program computes distance, EulerPhi, Psy, and Ysp. Program terminates when you enter points more than 10 apart")
    name=raw_input("Enter your name: ")
    keepLooping=True
    count = 0
    small = 10
    while keepLooping:
        user_input = raw_input("Enter Distance, Psy, Ysp, or EulerPhi: ")
        if (user_input=="Psy") or (user_input=="psy"):
            count +=1
            print'Loop iteration is: ', count
        elif (user_input=="Ysp") or (user_input=="ysp"):
            randNum = randint(1, 100)
            print'Perhaps you want to sing', randNum, 'Megan Trainor songs'
            count +=1
        elif(user_input=="EulerPhi")or (user_input=="eulerPhi"):
             num = int(input("Enter a number: "))
             for i in range(0,num):
                 if(relativePrime(i)):
                    print i,'is a Euler Phi for', num
                    count +=1
        elif (user_input=="Distance")or (user_input=="distance"):
            x1, y1, x2, y2 = map(int, raw_input("Enter 4 numbers separated by commas: ").split(','))
            d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            print 'The distance between', "(",x1,",",y1, ")" "and", "(",x2,",",y2, ") is", d
            count +=1
            if(d<small):
                small = d
            elif(d>=10):
                print "Thank you", name, "The smallest distance between points was", small
                keepLooping = False 
main()                     
           
