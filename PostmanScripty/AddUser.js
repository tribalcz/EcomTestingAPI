
const usersToAdd = [
    { id: "user001", username: "jannovak", email: "jan.novak@example.com", full_name: "Jan Novák" },
    { id: "user002", username: "petrsvoboda", email: "petr.svoboda@example.com", full_name: "Petr Svoboda" },
    { id: "user003", username: "marketakovacova", email: "marketa.kovacova@example.com", full_name: "Markéta Kovačová" },
    { id: "user004", username: "tomashorky", email: "tomas.horky@example.com", full_name: "Tomáš Horký" },
    { id: "user005", username: "evakralova", email: "eva.kralova@example.com", full_name: "Eva Králová" },
    { id: "user006", username: "martinanemcova", email: "martina.nemcova@example.com", full_name: "Martina Němcová" },
    { id: "user007", username: "lukasnovotny", email: "lukas.novotny@example.com", full_name: "Lukáš Novotný" },
    { id: "user008", username: "janaprochazkova", email: "jana.prochazkova@example.com", full_name: "Jana Procházková" },
    { id: "user009", username: "ondrejkolar", email: "ondrej.kolar@example.com", full_name: "Ondřej Kolář" },
    { id: "user010", username: "katerinasimkova", email: "katerina.simkova@example.com", full_name: "Kateřina Šimková" }
];

async function addUsers() {
    const url = 'http://localhost:9000/api/users/register';

    for (const user of usersToAdd) {
        try {
            const userData = {
                id: user.id,
                username: user.username,
                email: user.email,
                full_name: user.full_name,
                token: null,  // Toto pole bude generováno serverem
                is_activated: true,  // Výchozí hodnota
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };

            const response = await pm.sendRequest({
                url: url,
                method: 'POST',
                header: {
                    'Content-Type': 'application/json',
                },
                body: {
                    mode: 'raw',
                    raw: JSON.stringify(userData)
                }
            });

            if (response.code === 200) {
                console.log(`User added successfully: ${user.username}`);
            } else {
                console.error(`Failed to add user ${user.username}: ${response.status}`);
            }
        } catch (error) {
            console.error(`Error adding user ${user.username}: ${error.message}`);
        }
    }
}

// Volání funkce pro přidání uživatelů
addUsers();