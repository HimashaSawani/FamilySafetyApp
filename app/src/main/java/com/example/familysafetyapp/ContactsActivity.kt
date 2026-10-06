package com.example.familysafetyapp

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton

class ContactsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_contacts)

        findViewById<MaterialButton>(R.id.btnAddContact).setOnClickListener {
            Toast.makeText(this, "Add Guardian dialog: Enter name and phone number to sync with cloud.", Toast.LENGTH_SHORT).show()
        }
    }
}
