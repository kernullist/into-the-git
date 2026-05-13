function calculateTotal(items) {
    let total = 0;
    for (let i = 0; i < items.length; i++) {
        if (items[i] > 0) {
            total += items[i];
            if (items[i] > 100) {
                total += items[i] * 0.1;
            }
        }
    }
    return total;
}

class ShoppingCart {
    constructor() {
        this.items = [];
    }

    addItem(item, quantity) {
        if (quantity > 0) {
            this.items.push({ item, quantity });
        }
    }

    getItemCount() {
        let count = 0;
        for (let i = 0; i < this.items.length; i++) {
            count += this.items[i].quantity;
        }
        return count;
    }
}

module.exports = { calculateTotal, ShoppingCart };
