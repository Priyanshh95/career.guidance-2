#include <iostream>
using namespace std;

int main() {
    int num, reversed = 0, original, digit;
    cout << "Enter a number: ";  // Extra prompt added (causes partial mismatch)
    cin >> num;

    original = num;

    while (num > 0) {
        digit = num % 10;
        reversed = reversed * 10 + digit;
        num /= 10;
    }

    if (original == reversed)
        cout << original << " is a Palindrome number." << endl;  // Extra text
    else
        cout << original << " is Not a Palindrome number." << endl;

    return 0;
}
