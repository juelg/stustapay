package de.stustanet.stustapay.repository

import de.stustanet.stustapay.model.Account
import de.stustanet.stustapay.net.Response
import de.stustanet.stustapay.netsource.CustomerRemoteDataSource
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CustomerRepository @Inject constructor(
    private val customerRemoteDataSource: CustomerRemoteDataSource
) {
    suspend fun getCustomer(id: ULong): Response<Account> {
        return customerRemoteDataSource.getCustomer(id)
    }
}