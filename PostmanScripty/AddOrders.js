const userIds = Array.from({length: 10}, (_, i) => `user${(i + 1).toString().padStart(3, '0')}`);
const productIds = Array.from({length: 100}, (_, i) => `prod${(i + 1).toString().padStart(3, '0')}`);

function generateId() {
    return 'order' + Math.random().toString(36).substr(2, 9);
}

function generateOrder(index) {
    const userId = userIds[Math.floor(Math.random() * userIds.length)];
    const numProducts = Math.floor(Math.random() * 5) + 1; // 1 až 5 produktů v objednávce
    //Pokud byl vygenerován nový seznam produktů je nezbytné jejich identifikátory přidat do pole
    const products = [
        "prod-vzukvp808", "prod-r4hvsvl0e", "prod-sog4j2zd4", "prod-cl2wfjhmd",
        "prod-utc15sxhr", "prod-5ln6qwgz4", "prod-13a633cdd", "prod-2oghvr4r2",
        "prod-uxq0ffe0m", "prod-e8nefc67b", "prod-olv3b9cir", "prod-7tna9tdmr",
        "prod-frr3j7boh", "prod-xoxl9qerc", "prod-3vemd2rfl", "prod-yiiwjozaq",
        "prod-6f70xdmge", "prod-ehzrr29v4", "prod-tfwovxzit", "prod-1g783jdg4",
        "prod-rogjarnby", "prod-n3ocznynm", "prod-8u7zv6ugj", "prod-fuoigwbv8",
        "prod-xnapmpab9", "prod-mpx9g04wv", "prod-52n1tcddl", "prod-7eo253oi4",
        "prod-xiok201kl", "prod-debpmgn9m", "prod-cymhe9wlw", "prod-361831ht2",
        "prod-j95mf4n8n", "prod-doqoq5mnz", "prod-vlmutxpxt", "prod-aae8wm797",
        "prod-d3k8fky28", "prod-0sgxq13hp", "prod-xj5eku2ol", "prod-zhwqegfoh",
        "prod-glb1xm702", "prod-l0c5rvx20", "prod-1l6ub4qmj", "prod-is5a5cjex",
        "prod-ltlorvu8t", "prod-wua5bhoe6", "prod-4ml509ho4", "prod-96upbh961",
        "prod-cimvk30ul", "prod-2dwpdt27e", "prod-c9pzr1pzp", "prod-afnq9l05f",
        "prod-uviyg8x84", "prod-e7rqvou9a", "prod-1wbc28trs", "prod-s4owyquro",
        "prod-yu6endal8", "prod-x0fkq6ckj", "prod-l6dm4lray", "prod-oakzchdwi",
        "prod-qq3rtmlqr", "prod-uz4ffe9fo", "prod-a0vct54v6", "prod-cwca4h4cf",
        "prod-lsfmowbkq", "prod-b2rxmvdsn", "prod-0958yjjin", "prod-13rgci68k",
        "prod-lx425du89", "prod-m7befplps", "prod-qoqod2njv", "prod-fn34v0ht5",
        "prod-bo26jg4bi", "prod-axdoc729q", "prod-rwv7i2svm", "prod-d4pawprs3",
        "prod-a61482wjg", "prod-bi0sho841", "prod-eumrz3uph", "prod-eubvb59bw",
        "prod-768qbwukf", "prod-fhwg3radk", "prod-i0ru6399x", "prod-zyj491rri",
        "prod-wibbmqqo3", "prod-s3xujyff1", "prod-d77k81zcl", "prod-aq8hl3n23",
        "prod-n21ts0tiq", "prod-qmjc8dy4q", "prod-ibr4oqbv5", "prod-10dus2c64",
        "prod-hqvz13bp7", "prod-yop4ynnw7", "prod-vuwpx0ly0", "prod-ykxajwhq5",
        "prod-yccrwxpuh", "prod-vapt2is4z", "prod-ajvirqhw2", "prod-m1g0i41u7"
    ]

    const totalPrice = (Math.random() * 10000 + 500).toFixed(2); // Cena mezi 500 a 10500 Kč
    const statuses = ["new", "processing", "shipped", "delivered", "cancelled"];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const currentDate = new Date().toISOString();

    const randomCount = Math.floor(Math.random() * 100) + 1;

    // Náhodný výběr produktů
    const selectedProducts = [];
    while (selectedProducts.length < randomCount) {
        const randomIndex = Math.floor(Math.random() * products.length);
        if (!selectedProducts.includes(products[randomIndex])) {
            selectedProducts.push(products[randomIndex]);
        }
    }

    return {
        id: `order${(index + 1).toString().padStart(3, '0')}`,
        user_id: userId,
        products: selectedProducts,
        total_price: parseFloat(totalPrice),
        status: status,
        created_at: currentDate,
        updated_at: currentDate
    };
}

async function addOrders(count = 120) {
    const url = 'http://localhost:8000/api/orders/';
    const ordersToAdd = Array.from({length: count}, (_, i) => generateOrder(i));

    for (const order of ordersToAdd) {
        // Vypiš objednávku na konzoli pro kontrolu
        console.log('Generated Order Data:');
        console.log(JSON.stringify(order, null, 2));

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
                    raw: JSON.stringify(order, null, 2)
                }
            });

            // Zpracuj odpověď
            if (response.code === 200) {
                console.log(`Order added successfully: ${order.id}`);
            } else {
                console.error(`Failed to add order ${order.id}: Status ${response.code}`);
                console.error(`Response body: ${response.text()}`);
            }
        } catch (error) {
            console.error(`Error adding order ${order.id}: ${error.message}`);
        }

        // Přidáme krátkou pauzu mezi požadavky, aby se snížilo zatížení serveru
        await new Promise(resolve => setTimeout(resolve, 100));
    }
}

// Volání funkce pro přidání objednávek
addOrders(120);