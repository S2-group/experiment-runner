CXX = g++
CXXFLAGS = -std=c++11 -Wall -O2
TARGET = compressor

SRCS = main.cpp

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(SRCS) -o $(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all clean

