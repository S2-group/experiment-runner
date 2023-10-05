#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstring>
#include <unordered_map>

using namespace std;

const int MAX_DICT_SIZE = 4096;
const int MAX_STRING_LENGTH = 256;

class LZWCompressor {
public:
    LZWCompressor() {
        initializeDictionary();
    }

    void compress(istream& input, ostream& output) {
        int nextCode = 256;
        int currentCode = 0;
        string currentStr;
        char ch;

        while (input.get(ch)) {
            currentStr += ch;

            if (dictionary.find(currentStr) == dictionary.end()) {
                dictionary[currentStr] = nextCode++;
                currentStr.pop_back(); // Remove the last character
                outputCode(output, dictionary[currentStr]);
                if (nextCode < MAX_DICT_SIZE) {
                    dictionary[currentStr + ch] = nextCode++;
                }
                currentStr = ch;
            }
        }

        if (!currentStr.empty()) {
            outputCode(output, dictionary[currentStr]);
        }
    }

private:
    void initializeDictionary() {
        for (int i = 0; i < 256; ++i) {
            dictionary[string(1, char(i))] = i;
        }
    }

    void outputCode(ostream& output, int code) {
        unsigned char bytes[2];
        bytes[0] = code >> 8;
        bytes[1] = code & 0xFF;
        output.write(reinterpret_cast<char*>(bytes), sizeof(bytes));
    }

    unordered_map<string, int> dictionary;
};

int main(int argc, char* argv[]) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <output_filename> <input_filenames>" << endl;
        return 1;
    }

    string outputFileName = argv[1];
    vector<string> inputFiles;

    for (int i = 2; i < argc; ++i) {
        inputFiles.push_back(argv[i]);
    }

    ofstream outputFile(outputFileName, ios::binary);
    if (!outputFile) {
        cerr << "Error opening output file: " << outputFileName << endl;
        return 1;
    }

    LZWCompressor compressor;

    for (const string& inputFile : inputFiles) {
        ifstream inputFileStream(inputFile, ios::binary);
        if (!inputFileStream) {
            cerr << "Error opening input file: " << inputFile << endl;
            continue;
        }

        compressor.compress(inputFileStream, outputFile);
        inputFileStream.close();
    }

    outputFile.close();
    cout << "Compression completed. Output written to " << outputFileName << endl;

    return 0;
}

