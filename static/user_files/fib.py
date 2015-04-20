def fibonacci(n):

   if n == 0 or n == 1:
      return n
   else:

      # two recursive calls
      return fibonacci(n - 1) + fibonacci(n - 2)

number = int(raw_input("Enter an integer: "))

if number > 0:
   result = fibonacci(number)
   print "Fibonacci(%d) = %d" % ( number, result )
else:
   print "Cannot find the fibonacci of a negative number"
