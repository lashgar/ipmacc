    typedef int Node, Hash;

    void HashPrint(Hash* hash, void (*PrintFunc)(char*, char*))
    {
        unsigned int i;

        if (hash == NULL || hash->heads == NULL)
            return;

        for (i = 0; i < hash->table_size; ++i)
        {
            Node* temp = hash->heads[i];

            while (temp != NULL)
            {
                PrintFunc(temp->entry->key, temp->entry->value);
                temp = temp->next;
            }
        }
    }

