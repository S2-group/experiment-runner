with open('../input/closest_number.txt', 'w') as f:
    f.write(f"{350000000}\n")
    
    arr = range(-175000000, 175000000)  
    
    f.write(' '.join(map(str, arr)))
