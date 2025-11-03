// Sample JavaScript code for testing

function validateInput(input) {
    if (!input || input.trim() === '') {
        throw new Error('Input cannot be empty');
    }
    return input.trim();
}

class UserManager {
    constructor(database) {
        this.db = database;
        this.cache = new Map();
    }
    
    async getUser(userId) {
        if (this.cache.has(userId)) {
            return this.cache.get(userId);
        }
        
        const user = await this.db.query('SELECT * FROM users WHERE id = ?', [userId]);
        this.cache.set(userId, user);
        return user;
    }
    
    async createUser(userData) {
        const id = await this.db.insert('users', userData);
        return { id, ...userData };
    }
}

const processPayment = async (amount, paymentMethod) => {
    const result = await paymentService.charge(amount, paymentMethod);
    return result;
};

export { UserManager, validateInput, processPayment };
