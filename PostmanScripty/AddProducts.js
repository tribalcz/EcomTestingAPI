// Tento skript můžete použít v Postman nebo upravit pro použití v Node.js

const categories = ["nábytek", "psací potřeby", "papír", "organizace", "technika", "doplňky"];
const adjectives = ["Luxusní", "Ekonomický", "Ergonomický", "Moderní", "Klasický", "Barevný", "Praktický", "Skládací", "Multifunkční", "Elegantní"];
const products = [
    "Kancelářská židle", "Psací stůl", "Skříň", "Propisky", "Tužky", "Fixy", "Kancelářský papír", "Poznámkové bloky", "Sešity",
    "Pořadače", "Složky", "Šanony", "Počítač", "Monitor", "Klávesnice", "Myš", "Lampička", "Nástěnka", "Tabule", "Kalendář"
];

function generateId() {
    return 'prod-' + Math.random().toString(36).substr(2, 9);
}

function generateProduct() {
    const category = categories[Math.floor(Math.random() * categories.length)];
    const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const product = products[Math.floor(Math.random() * products.length)];
    const price = (Math.random() * 5000 + 50).toFixed(2);
    const stock = Math.floor(Math.random() * 100) + 1;

    return {
        id: generateId(),
        name: `${adjective} ${product}`,
        description: `${adjective} ${product.toLowerCase()} pro moderní kancelář`,
        price: parseFloat(price),
        stock: stock,
        category: category,
        is_available: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };
}

async function addProducts(count = 100) {
    const url = 'http://localhost:9000/api/products/';
    const productsToAdd = Array.from({length: count}, () => generateProduct());

    for (const product of productsToAdd) {
        try {
            const response = await pm.sendRequest({
                url: url,
                method: 'POST',
                header: {
                    'Content-Type': 'application/json',
                    'access_token': 'your-secret-api-key'  // Nahraďte svým skutečným API klíčem
                },
                body: {
                    mode: 'raw',
                    raw: JSON.stringify(product)
                }
            });

            if (response.code === 200) {
                console.log(`Product added successfully: ${product.name}`);
            } else {
                console.error(`Failed to add product ${product.name}: ${response.status}`);
            }
        } catch (error) {
            console.error(`Error adding product ${product.name}: ${error.message}`);
        }
    }
}

// Volání funkce pro přidání produktů
// Můžete změnit počet produktů podle potřeby, např. addProducts(50) pro 50 produktů
addProducts(100);