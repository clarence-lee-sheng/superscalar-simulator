a = [1,2,3,4,5,6,7,8,9,10]
b = [1,2,3,4,5,6,7,8,9,10]
c = [0,0,0,0,0,0,0,0,0,0]

for i in range(10): 
    c[i] = a[i] + b[i]

print(c)