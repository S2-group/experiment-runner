// C++ program to print all distinct pairs
// with given sum using three nested loops

#include <iostream>
#include <vector>
using namespace std;

// Function to find all possible pairs with the sum target
vector<vector<int> > distinctPairs(vector<int> &arr, int target) {
    vector<vector<int> > res;
    int n = arr.size();

    // Iterating over all possible pairs
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (arr[i] + arr[j] == target) {
                int first = min(arr[i], arr[j]);
                int second = max(arr[i], arr[j]);
                vector<int> cur = {first, second};
              
                  // Making sure that all pairs with target
                  // sum are distinct
                  if(find(res.begin(), res.end(), cur) == res.end())
                    res.push_back(cur);
            }
        }
    }

    return res;
}

int main() {
    vector<int> arr = {1, 5, 7, -1, 5};
    int target = 6;
    vector<vector<int> > res = distinctPairs(arr, target);

    for (int i = 0; i < res.size(); i++)
        cout << res[i][0] << " " << res[i][1] << endl;

    return 0;
}
