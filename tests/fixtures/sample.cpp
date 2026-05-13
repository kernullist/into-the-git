#include <iostream>
#include <vector>
#include <string>

class DataProcessor {
private:
    std::vector<int> data;
    std::string name;

public:
    DataProcessor(const std::string& n) : name(n) {}

    void addData(int value) {
        data.push_back(value);
    }

    int processData() {
        int total = 0;
        for (size_t i = 0; i < data.size(); i++) {
            if (data[i] > 0) {
                total += data[i];
                if (data[i] > 100) {
                    total += static_cast<int>(data[i] * 0.1);
                }
            } else if (data[i] < 0) {
                total -= data[i] / 2;
            }
        }
        return total;
    }

    void clearData() {
        data.clear();
    }

    const std::string& getName() const {
        return name;
    }
};

int main() {
    DataProcessor processor("test");
    for (int i = 0; i < 10; i++) {
        processor.addData(i * 10);
    }
    int result = processor.processData();
    std::cout << "Result: " << result << std::endl;
    return 0;
}
