TARGET = ./internals/warm_up
SRC = ./internals/warm_up.c

all: $(TARGET)

$(TARGET):
	gcc $(SRC) -o $(TARGET) -O2 -pthread -mavx2 -mfma

clean:
	rm -f $(TARGET) *.o